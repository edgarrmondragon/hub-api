from __future__ import annotations

import typing as t
from pathlib import Path

import sqlalchemy as sa
import yaml
from sqlalchemy.orm import Session as SessionBase
from sqlalchemy.orm import sessionmaker

from hub_api import enums, models
from hub_api.schemas import meltano, validation

if t.TYPE_CHECKING:
    from collections.abc import Generator


def get_default_variants(path: Path) -> dict[str, dict[str, str]]:
    """Get default variants of a given plugin."""
    with path.open() as f:
        return yaml.safe_load(f)  # type: ignore[no-any-return]


def get_plugin_variants(plugin_path: Path) -> Generator[tuple[str, dict[str, t.Any]]]:
    """Get plugin variants of a given type."""
    for plugin_file in plugin_path.glob("*.yml"):
        with plugin_file.open() as f:
            yield plugin_file.stem, yaml.safe_load(f)


def get_plugins_of_type(
    base_path: Path,
    plugin_type: enums.PluginTypeEnum,
) -> Generator[tuple[str, dict[str, t.Any]]]:
    """Get plugins of a given type."""
    for plugin_path in base_path.joinpath(plugin_type).glob("*"):
        yield from get_plugin_variants(plugin_path)


def _build_setting(variant_id: str, setting: meltano.PluginSetting) -> models.Setting:
    """Build setting object."""
    instance = models.Setting(
        id=f"{variant_id}.setting_{setting.root.name}",
        variant_id=variant_id,
        name=setting.root.name,
        label=setting.root.label,
        description=setting.root.description,
        env=setting.root.env,
        kind=setting.root.kind,
        value=setting.root.value,
        sensitive=setting.root.sensitive,
    )

    match setting.root:
        case meltano.OptionsSetting():
            instance.options = [opt.model_dump() for opt in setting.root.options]
        case _:
            pass

    return instance


def load_db(path: Path, session: SessionBase) -> None:  # noqa: C901, PLR0912, PLR0914, PLR0915
    """Load database."""

    default_variants = get_default_variants(path.joinpath("default_variants.yml"))
    maintainers = get_default_variants(path.joinpath("maintainers.yml"))

    for maintainer_id, maintainer_data in maintainers.items():
        maintainer_object = models.Maintainer(
            id=maintainer_id,
            name=maintainer_data.get("name"),
            label=maintainer_data.get("label"),
            url=maintainer_data.get("url"),
        )
        session.add(maintainer_object)

    for plugin_type in enums.PluginTypeEnum:
        for plugin_path in path.joinpath("meltano", plugin_type).glob("*"):
            default_variant = default_variants[plugin_type].get(plugin_path.name)
            plugin_id = f"{plugin_type}.{plugin_path.name}"
            default_variant_id = f"{plugin_id}.{default_variant}"

            for variant, definition in get_plugin_variants(plugin_path):
                plugin: validation.HubPluginDefinition
                match plugin_type:
                    case enums.PluginTypeEnum.extractors:
                        plugin = validation.ExtractorDefinition.model_validate(definition)
                    case enums.PluginTypeEnum.loaders:
                        plugin = validation.LoaderDefinition.model_validate(definition)
                    case enums.PluginTypeEnum.utilities:
                        plugin = validation.UtilityDefinition.model_validate(definition)
                    case enums.PluginTypeEnum.transformers:
                        plugin = validation.TransformerDefinition.model_validate(definition)
                    case enums.PluginTypeEnum.transforms:
                        plugin = validation.TransformDefinition.model_validate(definition)
                    case enums.PluginTypeEnum.orchestrators:
                        plugin = validation.OrchestratorDefinition.model_validate(definition)
                    case enums.PluginTypeEnum.mappers:
                        plugin = validation.MapperDefinition.model_validate(definition)
                    case enums.PluginTypeEnum.files:
                        plugin = validation.FileDefinition.model_validate(definition)
                    case _:
                        continue

                variant_id = f"{plugin_id}.{variant}"
                variant_object = models.PluginVariant(
                    plugin_id=plugin_id,
                    id=variant_id,
                    description=plugin.description,
                    executable=plugin.executable,
                    docs=str(plugin.docs) if plugin.docs else None,
                    name=variant,
                    label=plugin.label,
                    logo_url=plugin.logo_url,
                    pip_url=plugin.pip_url,
                    repo=str(plugin.repo),
                    ext_repo=str(plugin.ext_repo) if plugin.ext_repo else None,
                    namespace=plugin.namespace,
                    hidden=plugin.hidden,
                    maintenance_status=plugin.maintenance_status,
                    quality=plugin.quality,
                    domain_url=str(plugin.domain_url) if plugin.domain_url else None,
                    definition=plugin.definition,
                    next_steps=plugin.next_steps,
                    settings_preamble=plugin.settings_preamble,
                    usage=plugin.usage,
                    prereq=plugin.prereq,
                )
                session.add(variant_object)

                for setting in plugin.settings:
                    session.add(_build_setting(variant_id, setting))

                for group_idx, setting_group in enumerate(
                    definition.get("settings_group_validation", []),
                ):
                    for setting_name in setting_group:
                        setting_id = f"{variant_id}.setting_{setting_name}"
                        setting_group_object = models.RequiredSetting(
                            variant_id=variant_object.id,
                            setting_id=setting_id,
                            setting_name=setting_name,
                            group_id=group_idx,
                        )
                        session.add(setting_group_object)

                for capability in definition.get("capabilities", []):
                    capability_object = models.Capability(
                        id=f"{variant_id}.capability_{capability}",
                        variant_id=variant_object.id,
                        name=capability,
                    )
                    session.add(capability_object)

                for keyword in definition.get("keywords", []):
                    keyword_object = models.Keyword(
                        id=f"{variant_id}.keyword_{keyword}",
                        variant_id=variant_object.id,
                        name=keyword,
                    )
                    session.add(keyword_object)

                for i, select in enumerate(definition.get("select", [])):
                    select_object = models.Select(
                        id=f"{variant_id}.select_{i}",
                        variant_id=variant_object.id,
                        expression=select,
                    )
                    session.add(select_object)

                for i, (key, metadata) in enumerate(definition.get("metadata", {}).items()):
                    metadata_object = models.Metadata(
                        id=f"{variant_id}.metadata_{i}",
                        variant_id=variant_object.id,
                        key=key,
                        value=metadata,
                    )
                    session.add(metadata_object)

                for command_name, command in definition.get("commands", {}).items():
                    command_id = f"{variant_id}.command_{command_name}"
                    if isinstance(command, str):
                        command_object = models.Command(
                            id=command_id,
                            variant_id=variant_object.id,
                            name=command_name,
                            args=command,
                        )
                    else:
                        command_object = models.Command(
                            id=command_id,
                            variant_id=variant_object.id,
                            name=command_name,
                            args=command.get("args"),
                            description=command.get("description"),
                            executable=command.get("executable"),
                        )
                    session.add(command_object)

            default_variant_object = models.Plugin(
                id=plugin_id,
                default_variant_id=default_variant_id,
                plugin_type=plugin_type.value,
                name=plugin_path.name,
            )
            session.add(default_variant_object)

    session.commit()


if __name__ == "__main__":
    import sys

    engine = sa.create_engine("sqlite:///plugins.db")
    SyncSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SyncSession()

    models.EntityBase.metadata.drop_all(engine)
    models.EntityBase.metadata.create_all(engine)

    hub_data = sys.argv[1] if len(sys.argv) > 1 else "../../meltano/hub/_data"
    load_db(Path(hub_data).resolve(), session)
