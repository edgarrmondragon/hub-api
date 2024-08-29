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


class ExtractorCapabilityEnum(enum.StrEnum):
    """Extractor capabilities."""

    properties = enum.auto()
    catalog = enum.auto()
    discover = enum.auto()
    state = enum.auto()
    about = enum.auto()
    stream_maps = "stream-maps"
    schema_flattening = "schema-flattening"
    activate_version = "activate-version"
    batch = enum.auto()
    test = enum.auto()
    log_based = "log-based"


class LoaderCapabilityEnum(enum.StrEnum):
    """Loader capabilities."""

    about = enum.auto()
    stream_maps = "stream-maps"
    schema_flattening = "schema-flattening"
    hard_delete = "hard-delete"
