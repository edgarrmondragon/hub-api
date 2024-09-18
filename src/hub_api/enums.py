from __future__ import annotations

import enum


class PluginTypeEnum(enum.StrEnum):
    """Plugin types."""

    extractors = enum.auto()
    loaders = enum.auto()
    transformers = enum.auto()
    utilities = enum.auto()
    transforms = enum.auto()
    orchestrators = enum.auto()
    mappers = enum.auto()
    files = enum.auto()


class MaintenanceStatusEnum(enum.StrEnum):
    """Maintenance statuses."""

    active = enum.auto()
    beta = enum.auto()
    development = enum.auto()
    inactive = enum.auto()
    unknown = enum.auto()


class QualityEnum(enum.StrEnum):
    """Quality levels."""

    gold = enum.auto()
    silver = enum.auto()
    bronze = enum.auto()
    unknown = enum.auto()


class _HyphenatedEnum(enum.StrEnum):
    """Base class for hyphenated enums."""

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[str]) -> str:  # noqa: ARG004
        return name.lower().replace("_", "-")


class ExtractorCapabilityEnum(_HyphenatedEnum):
    """Extractor capabilities."""

    properties = enum.auto()
    catalog = enum.auto()
    discover = enum.auto()
    state = enum.auto()
    about = enum.auto()
    stream_maps = enum.auto()
    schema_flattening = enum.auto()
    activate_version = enum.auto()
    batch = enum.auto()
    test = enum.auto()
    log_based = enum.auto()


class LoaderCapabilityEnum(_HyphenatedEnum):
    """Loader capabilities."""

    about = enum.auto()
    activate_version = enum.auto()
    datatype_failsafe = enum.auto()
    hard_delete = enum.auto()
    schema_flattening = enum.auto()
    soft_delete = enum.auto()
    stream_maps = enum.auto()
    validate_records = enum.auto()


class MapperCapabilityEnum(_HyphenatedEnum):
    """Mapper capabilities."""

    stream_maps = enum.auto()
