from __future__ import annotations

import typing as t
from pathlib import Path

import sqlalchemy as sa
import yaml
from sqlalchemy.orm import Session as SessionBase
from sqlalchemy.orm import sessionmaker

from hub_api import models


def get_default_variants(path: Path) -> dict[str, dict[str, str]]:
    """Get default variants of a given plugin."""
    with path.open() as f:
        return yaml.safe_load(f)


def get_plugin_variants(plugin_path: Path) -> t.Generator[tuple[str, dict], None, None]:
    """Get plugin variants of a given type."""
    for plugin_file in plugin_path.glob("*.yml"):
        with plugin_file.open() as f:
            yield plugin_file.stem, yaml.safe_load(f)


def get_plugins_of_type(
    base_path: Path,
    plugin_type: models.PluginType,
) -> t.Generator[tuple[str, dict], None, None]:
    """Get plugins of a given type."""
    for plugin_path in base_path.joinpath(plugin_type).glob("*"):
        yield from get_plugin_variants(plugin_path)


def load_db(path: Path, session: SessionBase) -> None:  # noqa: C901
    """Load database."""

    default_variants = get_default_variants(path.joinpath("default_variants.yml"))

    for plugin_type in models.PluginType:
        for plugin_path in path.joinpath("meltano", plugin_type).glob("*"):
            default_variant = default_variants[plugin_type].get(plugin_path.name)
            plugin_id = f"{plugin_type}.{plugin_path.name}"
            default_variant_id = f"{plugin_id}.{default_variant}"  # noqa: F841

            for variant, definition in get_plugin_variants(plugin_path):
                variant_id = f"{plugin_id}.{variant}"
                variant_object = models.PluginVariant(
                    plugin_id=plugin_id,
                    id=variant_id,
                    description=definition.get("description"),
                    executable=definition.get("executable"),
                    docs=definition.get("docs"),
                    name=variant,
                    label=definition.get("label"),
                    logo_url=definition.get("logo_url"),
                    pip_url=definition.get("pip_url"),
                    repo=definition.get("repo"),
                    ext_repo=definition.get("ext_repo"),
                    namespace=definition.get("namespace"),
                    hidden=definition.get("hidden"),
                    maintenance_status=definition.get("maintenance_status"),
                    quality=definition.get("quality"),
                    domain_url=definition.get("domain_url"),
                    definition=definition.get("definition"),
                    next_steps=definition.get("next_steps"),
                    settings_preamble=definition.get("settings_preamble"),
                    usage=definition.get("usage"),
                    prereq=definition.get("prereq"),
                )
                session.add(variant_object)

                for setting in definition.get("settings", []):
                    setting_object = models.Setting(
                        id=f"{variant_id}.setting_{setting['name']}",
                        variant_id=variant_object.id,
                        name=setting["name"],
                        label=setting.get("label"),
                        description=setting.get("description"),
                        env=setting.get("env"),
                        kind=setting.get("kind"),
                        value=setting.get("value"),
                        options=setting.get("options"),
                        sensitive=setting.get("sensitive"),
                    )
                    session.add(setting_object)

                for group_idx, setting_group in enumerate(
                    definition.get("settings_group_validation", []),
                ):
                    for setting_name in setting_group:
                        setting_id = f"{variant_id}.setting_{setting_name}"
                        setting_group_object = models.RequiredSetting(
                            variant_id=variant_object.id,
                            setting_id=setting_id,
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
                default_variant_id=f"{plugin_id}.{default_variant}",
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
