from __future__ import annotations

import dataclasses
import gzip
import json
import logging
import shutil
import sqlite3
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, assert_never

import platformdirs
import pydantic
import requests
import yaml
from sqlalchemy.dialects import sqlite
from sqlalchemy.schema import CreateTable

from hub_api import enums, models
from hub_api.schemas import meltano, validation

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    import pydantic_core

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

sqlite3.register_adapter(list, json.dumps)
sqlite3.register_adapter(dict, json.dumps)


def download_meltano_hub_archive(*, ref: str = "main", use_cache: bool = True) -> Path:
    """Download Meltano Hub archive."""
    cached_tree = Path(platformdirs.user_cache_dir()) / "hub-api"
    if use_cache and cached_tree.exists():
        logger.info("Using cached directory %s", cached_tree)

    else:
        shutil.rmtree(cached_tree, ignore_errors=True)
        url = f"https://github.com/meltano/hub/archive/{ref}.tar.gz"
        logger.info("Downloading archive %s", url)

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".tar.gz") as tmp_file:
            tmp_file.write(gzip.decompress(response.content))
            tmp_file.seek(0)
            with tempfile.TemporaryDirectory() as extract_dir, tarfile.open(tmp_file.name) as tar:
                tar.extractall(extract_dir, filter="data")
                extracted = tar.getnames()[0]

                # Move each item in the extracted directory to the cache
                extracted_dir = Path(extract_dir) / extracted
                cached_tree.mkdir(parents=True)
                for item in extracted_dir.iterdir():
                    shutil.move(item, cached_tree / item.name)

    return cached_tree


def get_default_variants(path: Path) -> dict[str, dict[str, str]]:
    """Get default variants of a given plugin."""
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)  # type: ignore[no-any-return]


def get_plugin_variants(
    plugin_path: Path,
) -> Generator[tuple[str, dict[str, Any]]]:
    """Get plugin variants of a given type."""
    for plugin_file in plugin_path.glob("*.yml"):
        with plugin_file.open() as f:
            yield plugin_file.stem, yaml.safe_load(f)


def get_plugins_of_type(
    base_path: Path,
    plugin_type: enums.PluginTypeEnum,
) -> Generator[tuple[str, dict[str, Any]]]:
    """Get plugins of a given type."""
    for plugin_path in base_path.joinpath(plugin_type).glob("*"):
        yield from get_plugin_variants(plugin_path)


def _build_setting(
    variant_id: str,
    setting: meltano.PluginSetting,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Build setting object."""
    setting_id = f"{variant_id}.setting_{setting.root.name}"
    setting_data: dict[str, Any] = {
        "id": setting_id,
        "variant_id": variant_id,
        "name": setting.root.name,
        "label": setting.root.label,
        "documentation": setting.root.documentation,
        "description": setting.root.description,
        "placeholder": setting.root.placeholder,
        "env": setting.root.env,
        "kind": setting.root.kind,
        "value": None if setting.root.value is None else json.dumps(setting.root.value),
        "sensitive": setting.root.sensitive,
        "options": None,
    }

    match setting.root:
        case meltano.OptionsSetting():
            setting_data["options"] = [opt.model_dump() for opt in setting.root.options]
        case _:
            pass

    aliases_data: list[dict[str, Any]] = []
    if setting.root.aliases:
        aliases_data.extend(
            {
                "id": f"{setting_id}.alias_{alias}",
                "setting_id": setting_id,
                "name": alias,
            }
            for alias in setting.root.aliases
        )

    return setting_data, aliases_data


@dataclasses.dataclass
class LoadError:
    plugin_name: str
    variant: str
    link: str
    error: pydantic_core.ErrorDetails


@dataclasses.dataclass
class LoadResult:
    errors: list[LoadError]

    def to_markdown(self) -> str:
        """Convert errors to a markdown table."""
        result = "## Build Errors\n\n| Plugin | Error | Value | Location |\n"
        result += "|--------|---------|------|----------|\n"
        result += "\n".join([
            (
                f"| [{error.variant}/{error.plugin_name}]({error.link}) "
                f"| {error.error['msg']} | {error.error['input']} "
                f"| {error.error['loc']} |"
            )
            for error in self.errors
        ])
        return result


def _insert_row(connection: sqlite3.Connection, table: str, row: dict[str, Any]) -> None:
    """Insert a row into the specified table."""
    column_names = row.keys()
    columns = ", ".join(column_names)
    placeholders = ", ".join(f":{col}" for col in column_names)
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"  # noqa: S608
    connection.execute(query, row)


def _insert_rows(connection: sqlite3.Connection, table: str, rows: Sequence[dict[str, Any]]) -> None:
    """Insert multiple rows into the specified table."""
    column_names = rows[0].keys()
    columns = ", ".join(column_names)
    placeholders = ", ".join(f":{col}" for col in column_names)
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"  # noqa: S608
    connection.executemany(query, rows)


def load_db(  # noqa: C901, PLR0912, PLR0914, PLR0915
    path: Path,
    connection: sqlite3.Connection,
) -> LoadResult:
    """Load database."""
    result = LoadResult(errors=[])
    default_variants = get_default_variants(path.joinpath("default_variants.yml"))
    maintainers = get_default_variants(path.joinpath("maintainers.yml"))

    for maintainer_id, maintainer_data in maintainers.items():
        _insert_row(
            connection,
            "maintainers",
            {
                "id": maintainer_id,
                "name": maintainer_data.get("name"),
                "label": maintainer_data.get("label"),
                "url": maintainer_data.get("url"),
            },
        )

    for plugin_type in enums.PluginTypeEnum:
        variant_count = 0  # Counter for processed plugin variants
        plugin_count = 0  # Counter for processed plugins
        for plugin_path in path.joinpath("meltano", plugin_type).glob("*"):
            plugin_name = plugin_path.name
            default_variant = default_variants[plugin_type].get(plugin_name)
            plugin_id = f"{plugin_type}.{plugin_name}"
            default_variant_id = f"{plugin_id}.{default_variant}"

            for variant, definition in get_plugin_variants(plugin_path):
                plugin: validation.HubPluginDefinition
                try:
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
                            assert_never(plugin_type)
                except pydantic.ValidationError as exc:
                    logger.error("Error validating plugin %s", plugin_id)
                    for error in exc.errors():
                        result.errors.append(
                            LoadError(
                                plugin_name=plugin_name,
                                variant=variant,
                                link=f"https://github.com/meltano/hub/blob/main/_data/meltano/{plugin_type}/{plugin_name}/{variant}.yml",
                                error=error,
                            ),
                        )
                    continue

                variant_id = f"{plugin_id}.{variant}"
                _insert_row(
                    connection,
                    "plugin_variants",
                    {
                        "plugin_id": plugin_id,
                        "id": variant_id,
                        "description": plugin.description,
                        "executable": plugin.executable,
                        "docs": str(plugin.docs) if plugin.docs else None,
                        "name": variant,
                        "label": plugin.label,
                        "logo_url": plugin.logo_url,
                        "pip_url": plugin.pip_url,
                        "repo": str(plugin.repo),
                        "ext_repo": str(plugin.ext_repo) if plugin.ext_repo else None,
                        "namespace": plugin.namespace,
                        "hidden": plugin.hidden,
                        "maintenance_status": plugin.maintenance_status.value if plugin.maintenance_status else None,
                        "quality": plugin.quality.value if plugin.quality else None,
                        "domain_url": str(plugin.domain_url) if plugin.domain_url else None,
                        "definition": plugin.definition,
                        "next_steps": plugin.next_steps,
                        "settings_preamble": plugin.settings_preamble,
                        "usage": plugin.usage,
                        "prereq": plugin.prereq,
                    },
                )
                variant_count += 1

                for setting in plugin.settings:
                    setting_data, aliases_data = _build_setting(variant_id, setting)
                    _insert_row(connection, "settings", setting_data)
                    if aliases_data:
                        _insert_rows(connection, "setting_aliases", aliases_data)

                for group_idx, setting_group in enumerate(
                    definition.get("settings_group_validation", []),
                ):
                    for setting_name in setting_group:
                        setting_id = f"{variant_id}.setting_{setting_name}"
                        _insert_row(
                            connection,
                            "setting_groups",
                            {
                                "variant_id": variant_id,
                                "setting_id": setting_id,
                                "setting_name": setting_name,
                                "group_id": group_idx,
                            },
                        )

                for capability in definition.get("capabilities", []):
                    _insert_row(
                        connection,
                        "capabilities",
                        {
                            "id": f"{variant_id}.capability_{capability}",
                            "variant_id": variant_id,
                            "name": capability,
                        },
                    )

                for keyword in definition.get("keywords", []):
                    _insert_row(
                        connection,
                        "keywords",
                        {
                            "id": f"{variant_id}.keyword_{keyword}",
                            "variant_id": variant_id,
                            "name": keyword,
                        },
                    )

                for i, select in enumerate(definition.get("select", [])):
                    _insert_row(
                        connection,
                        "selects",
                        {
                            "id": f"{variant_id}.select_{i}",
                            "variant_id": variant_id,
                            "expression": select,
                        },
                    )

                for i, (key, metadata) in enumerate(
                    definition.get("metadata", {}).items(),
                ):
                    _insert_row(
                        connection,
                        "metadata",
                        {
                            "id": f"{variant_id}.metadata_{i}",
                            "variant_id": variant_id,
                            "key": key,
                            "value": metadata,
                        },
                    )

                for command_name, command in definition.get("commands", {}).items():
                    command_id = f"{variant_id}.command_{command_name}"
                    if isinstance(command, str):
                        command_details = {
                            "id": command_id,
                            "variant_id": variant_id,
                            "name": command_name,
                            "args": command,
                        }
                    else:
                        command_details = {
                            "id": command_id,
                            "variant_id": variant_id,
                            "name": command_name,
                            "args": command.get("args"),
                            "description": command.get("description"),
                            "executable": command.get("executable"),
                        }
                    _insert_row(connection, "commands", command_details)

            _insert_row(
                connection,
                "plugins",
                {
                    "id": plugin_id,
                    "default_variant_id": default_variant_id,
                    "plugin_type": plugin_type.value,
                    "name": plugin_name,
                },
            )
            plugin_count += 1

        logger.info(
            "Processed %d variants for %d unique %s",
            variant_count,
            plugin_count,
            plugin_type.value,
        )

    connection.commit()
    return result


def main() -> int:
    import argparse  # noqa: PLC0415

    from hub_api import database  # noqa: PLC0415

    class CLINamespace(argparse.Namespace):
        git_ref: str
        cache: bool
        exit_zero: bool

    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--git-ref", default="main")
    parser.add_argument("--no-cache", action="store_false", dest="cache")
    parser.add_argument("--exit-zero", action="store_true", dest="exit_zero")

    db_path = database.get_db_path()
    db_path.unlink(missing_ok=True)

    with sqlite3.connect(db_path) as connection:
        for table in models.EntityBase.metadata.sorted_tables:
            connection.execute(str(CreateTable(table).compile(dialect=sqlite.dialect())))  # type: ignore[no-untyped-call]

        args = parser.parse_args(namespace=CLINamespace())

        hub_dir = download_meltano_hub_archive(ref=args.git_ref, use_cache=args.cache)
        result = load_db(hub_dir / "_data", connection)
        print(result.to_markdown())

    return 0 if args.exit_zero else 1 if result.errors else 0


if __name__ == "__main__":
    sys.exit(main())
