"""Response schemas for the API."""

import enum
from typing import Dict, List

from pydantic import BaseModel, Field


class VariantReference(BaseModel):
    """Variant reference model."""

    ref: str = Field(description="API URL for the variant")


class Plugin(BaseModel):
    """Plugin entry."""

    logo_url: str = Field(description="URL to the plugin's logo")
    default_variant: str = Field(description="The default variant of the plugin")
    variants: Dict[str, VariantReference] = Field(
        description="The variants of the plugin",
    )


class PluginIndex(BaseModel):
    """Plugin index model."""

    __root__: Dict[str, Plugin]


class SettingKind(str, enum.Enum):
    """A valid plugin setting kind."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    PASSWORD = "password"
    DATE_ISO8601 = "date_iso8601"


class PluginSetting(BaseModel):
    """Plugin setting model."""

    name: str = Field(description="The setting name.", example="token")
    description: str = Field(
        default="",
        description="The setting description.",
        example="The API token.",
    )
    label: str = Field(description="The setting label.", example="API Token")
    kind: SettingKind = Field(
        default=SettingKind.STRING,
        description="The setting kind.",
        example=SettingKind.PASSWORD,
    )


class BasePluginDetails(BaseModel):
    """Base plugin details model."""

    name: str = Field(description="The plugin name", example="tap-csv")
    description: str = Field(
        default="",
        description="The plugin description",
        example="A Singer tap for CSV files.",
    )
    label: str = Field(description="The plugin label", example="CSV Tap")
    pip_url: str = Field(
        title="Pip URL",
        description=(
            "A string containing the command line arguments to pass to `pip install`. "
            "See https://pip.pypa.io/en/stable/cli/pip_install/#usage for more "
            "information."
        ),
        examples=[
            "git+https://github.com/singer-io/tap-github.git",
            "pipelinewise-tap-mysql",
            "-e path/to/local/tap",
        ],
    )
    namespace: str
    variant: str = Field(
        description="The plugin variant",
        example="meltanolabs",
    )
    settings: List[PluginSetting]
