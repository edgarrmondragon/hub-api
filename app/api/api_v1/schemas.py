"""Response schemas for the API."""

from __future__ import annotations

import enum
import typing as t

from pydantic import BaseModel, Field, RootModel


class VariantReference(BaseModel):
    """Variant reference model."""

    ref: str = Field(description="API URL for the variant")


class Plugin(BaseModel):
    """Plugin entry."""

    # logo_url: str = Field(description="URL to the plugin's logo")
    default_variant: str = Field(description="The default variant of the plugin")
    variants: dict[str, VariantReference] = Field(
        description="The variants of the plugin",
    )


class PluginIndex(RootModel):
    """Plugin index model."""


class SettingKind(str, enum.Enum):
    """A valid plugin setting kind."""

    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DATE_ISO8601 = "date_iso8601"
    EMAIL = "email"
    PASSWORD = "password"  # noqa: S105
    OAUTH = "oauth"
    OPTIONS = "options"
    FILE = "file"
    ARRAY = "array"
    OBJECT = "object"
    HIDDEN = "hidden"


class _BasePluginSetting(BaseModel):
    """Plugin setting model."""

    name: str = Field(
        description="The setting name.",
        json_schema_extra={"example": "token"},
    )
    description: str = Field(
        default="",
        description="The setting description.",
        examples=["The API token."],
    )
    # label: str = Field(description="The setting label.", examples=["API Token"])
    # kind: SettingKind | None = Field(
    #     default=SettingKind.STRING,
    #     description="The setting kind.",
    #     examples=[SettingKind.PASSWORD],
    # )


class StringSetting(_BasePluginSetting):
    """String setting model."""

    kind: t.Literal["string"]


class IntegerSetting(_BasePluginSetting):
    """Integer setting model."""

    kind: t.Literal["integer"]


class BooleanSetting(_BasePluginSetting):
    """Boolean setting model."""

    kind: t.Literal["boolean"]


class DateIso8601Setting(_BasePluginSetting):
    """Date ISO8601 setting model."""

    kind: t.Literal["date_iso8601"]


class EmailSetting(_BasePluginSetting):
    """Email setting model."""

    kind: t.Literal["email"]


class PasswordSetting(_BasePluginSetting):
    """Password setting model."""

    kind: t.Literal["password"]


class OAuthSetting(_BasePluginSetting):
    """OAuth setting model."""

    kind: t.Literal["oauth"]


class Option(BaseModel):
    """Option model."""

    value: str = Field(description="The option value")
    label: str = Field(description="The option label")


class OptionsSetting(_BasePluginSetting):
    """Options setting model."""

    kind: t.Literal["options"]
    options: list[Option] = Field(
        description="The setting options",
        default_factory=list,
    )


class FileSetting(_BasePluginSetting):
    """File setting model."""

    kind: t.Literal["file"]


class ArraySetting(_BasePluginSetting):
    """Array setting model."""

    kind: t.Literal["array"]


class ObjectSetting(_BasePluginSetting):
    """Object setting model."""

    kind: t.Literal["object"]


class HiddenSetting(_BasePluginSetting):
    """Hidden setting model."""

    kind: t.Literal["hidden"]


class PluginSetting(RootModel):
    root: (
        StringSetting
        | IntegerSetting
        | BooleanSetting
        | DateIso8601Setting
        | EmailSetting
        | PasswordSetting
        | OAuthSetting
        | OptionsSetting
        | FileSetting
        | ArraySetting
        | ObjectSetting
        | HiddenSetting
    ) = Field(
        description="The setting kind.",
        discriminator="kind",
    )


class BasePluginDetails(BaseModel):
    """Base plugin details model."""

    name: str = Field(description="The plugin name", examples=["tap-csv"])
    description: str = Field(
        default="",
        description="The plugin description",
        examples=["A Singer tap for CSV files."],
    )
    # label: str = Field(description="The plugin label", examples=["CSV Tap"])
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
        examples=["meltanolabs"],
    )
    # logo_url: str | None = Field(
    #     description="URL to the plugin's logo",
    #     examples=["https://meltano.com/images/logo.png"],
    # )
    repo: str = Field(description="The plugin repository")
    settings_group_validation: list[list[str]] = Field(
        default_factory=list,
        description="A list of lists of setting names that must be set together.",
    )
    settings: list[PluginSetting]
    capabilities: list[str]
    keywords: list[str]

    # maintenance_status: str = "active"
