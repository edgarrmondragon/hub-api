from __future__ import annotations

import typing as t
from pathlib import Path

import sqlalchemy as sa
import yaml
from sqlalchemy.orm import Session as SessionBase
from sqlalchemy.orm import sessionmaker

from app.api.api_v1.endpoints.plugins import PluginType
from app.models import Capability, EntityBase, Keyword, Plugin, PluginVariant, Setting


def get_default_variants(path: Path) -> list[Path]:
    """Get default variants of a given plugin."""
    with open(path) as f:
        return yaml.safe_load(f)


def get_plugin_variants(plugin_path: Path) -> t.Generator[tuple[str, dict], None, None]:
    """Get plugin variants of a given type."""
    for plugin_file in plugin_path.glob("*.yml"):
        with open(plugin_file) as f:
            yield plugin_file.stem, yaml.safe_load(f)


def get_plugins_of_type(
    base_path: Path,
    plugin_type: PluginType,
) -> t.Generator[tuple[str, dict], None, None]:
    """Get plugins of a given type."""
    for plugin_path in base_path.joinpath(plugin_type.value).glob("*"):
        yield from get_plugin_variants(plugin_path)


def load_db(path: Path, session: SessionBase) -> None:
    """Load database."""

    default_variants = get_default_variants(path.joinpath("default_variants.yml"))

    for plugin_type in PluginType:
        for plugin_path in path.joinpath("meltano", plugin_type.value).glob("*"):
            default_variant = default_variants[plugin_type.value].get(plugin_path.name)
            plugin_id = f"{plugin_type.value}.{plugin_path.name}"
            default_variant_id = f"{plugin_id}.{default_variant}"  # noqa: F841

            for variant, definition in get_plugin_variants(plugin_path):
                variant_id = f"{plugin_id}.{variant}"
                plugin_object = PluginVariant(
                    id=variant_id,
                    plugin_id=plugin_id,
                    name=variant,
                    pip_url=definition.get("pip_url"),
                    repo=definition.get("repo"),
                    namespace=definition.get("namespace"),
                )
                session.add(plugin_object)

                for setting in definition.get("settings", []):
                    setting_object = Setting(
                        id=f"{variant_id}.{setting['name']}",
                        variant_id=variant_id,
                        name=setting["name"],
                        label=setting.get("label"),
                        description=setting.get("description"),
                        kind=setting.get("kind"),
                        value=setting.get("value"),
                    )
                    session.add(setting_object)

                for capability in definition.get("capabilities", []):
                    capability_object = Capability(
                        id=f"{variant_id}.{capability}",
                        variant_id=variant_id,
                        name=capability,
                    )
                    session.add(capability_object)

                for keyword in definition.get("keywords", []):
                    keyword_object = Keyword(
                        id=f"{variant_id}.{keyword}",
                        variant_id=variant_id,
                        name=keyword,
                    )
                    session.add(keyword_object)

            default_variant_object = Plugin(
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

    EntityBase.metadata.drop_all(engine)
    EntityBase.metadata.create_all(engine)

    hub_data = sys.argv[1] if len(sys.argv) > 1 else "../../meltano/hub/_data"
    load_db(Path(hub_data).resolve(), session)
