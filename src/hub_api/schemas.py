"""Response schemas for the API."""

from __future__ import annotations

import enum
import typing as t

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field, HttpUrl, RootModel

from . import enums


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(from_attributes=True)


class VariantReference(BaseModel):
    """Variant reference model."""

    ref: str = Field(
        description="API URL for the variant",
        examples=["https://hub.meltano.com/meltano/api/v1/plugins/extractors/tap-github--singer-io"],
    )


class Plugin(BaseModel):
    """Plugin entry."""

    default_variant: str = Field(description="The default variant of the plugin", examples=["singer-io"])
    variants: dict[str, VariantReference] = Field(description="The variants of the plugin", default_factory=dict)
    logo_url: str | None = Field(None, description="URL to the plugin's logo")


type PluginTypeIndex = dict[str, Plugin]
type PluginIndex = dict[enums.PluginTypeEnum, PluginTypeIndex]


class SettingKind(enum.StrEnum):
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

    aliases: list[str] | None = None
    description: str | None = Field(
        None,
        description="The setting description.",
        examples=["The API token."],
    )
    env: str | None = Field(None, description="The environment variable name.")
    label: str | None = Field(
        description="The setting label.",
        examples=["API Token"],
    )
    name: str = Field(
        description="The setting name.",
        json_schema_extra={"example": "token"},
    )
    sensitive: bool | None = Field(
        description="Whether the setting is sensitive.",
    )
    value: t.Any | None = Field(None, description="The setting value.")


class StringSetting(_BasePluginSetting):
    """String setting model."""

    kind: t.Literal["string", None]


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


class Command(BaseModel):
    """Command model."""

    args: str = Field(description="Command arguments")
    description: str | None = Field(
        None,
        description="Documentation displayed when listing commands",
    )
    executable: str | None = Field(
        None,
        description="Override the plugin's executable for this command",
    )

    # TODO: Fill the container_spec field
    container_spec: dict[str, t.Any] | None = Field(
        None,
        description="Container specification for this command",
    )


class PluginRequires(BaseModel):
    """Plugin requires model."""

    name: str = Field(description="The required plugin name")
    variant: str = Field(description="The required plugin variant")


class BasePluginDetails(BaseModel):
    """Base plugin details model."""

    name: str = Field(description="The plugin name", examples=["tap-csv"])
    namespace: str
    label: str | None = Field(description="The plugin label", examples=["CSV Tap"])
    description: str | None = Field(
        None,
        description="The plugin description",
        examples=["A Singer tap for CSV files."],
    )
    docs: HttpUrl | None = Field(
        None,
        description="A URL to the documentation for this plugin",
    )
    variant: str = Field(
        description="The plugin variant",
        examples=["meltanolabs"],
    )
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
    logo_url: HttpUrl | None = Field(
        description="URL to the plugin's logo",
        examples=["https://meltano.com/images/logo.png"],
    )
    executable: str | None = Field(
        None,
        description="The plugin's executable name, as defined in setup.py (if a Python based " "plugin)",
        examples=[
            "tap-stripe",
            "tap-covid-19",
        ],
    )
    repo: HttpUrl = Field(description="The plugin repository")
    ext_repo: HttpUrl | None = Field(
        None,
        description="The URL to the repository where the plugin extension code lives.",
    )
    python: str | None = Field(
        None,
        description=(
            "The python version to use for this plugin, specified as a path, or as "
            "the name of an executable to find within a directory in $PATH. If not "
            "specified, the top-level `python` setting will be used, or if it is not "
            "set, the python executable that was used to run Meltano will be used "
            "(within a separate virtual environment)."
        ),
        examples=[
            "/usr/bin/python3.10",
            "python",
            "python3.11",
        ],
    )

    settings_group_validation: list[list[str]] = Field(
        default_factory=list,
        description="A list of lists of setting names that must be set together.",
    )

    settings: list[PluginSetting]
    commands: dict[str, str | Command] = Field(
        default_factory=dict,
        description=(
            "An object containing commands to be run by the plugin, the keys are the "
            "name of the command and the values are the arguments to be passed to the "
            "plugin executable."
        ),
    )
    requires: list[PluginRequires] = Field(default_factory=list)

    hidden: bool | None = Field(
        None,
        description="Whether the plugin should be shown when listing or not.",
    )

    domain_url: HttpUrl | None = Field(
        None,
        description="Links to the website represnting the database, api, etc.",
    )
    definition: str | None = Field(
        None,
        description="A brief description of the plugin.",
    )
    next_steps: str | None = Field(
        None,
        description=(
            "A markdown string that gets added after the auto generated installation "
            "section. Commonly used for next steps following "
            "installation/configuration i.e. how to turn on a service or init a system "
            "database."
        ),
    )
    settings_preamble: str | None = Field(
        None,
        description=(
            "A markdown string that gets added to the beginning of the setting section "
            "on the plugin pages. Commonly used for adding notes on advanced settings."
        ),
    )
    usage: str | None = Field(
        None,
        description=(
            "A markdown string that gets appended to the bottom of the plugin pages. "
            "Commonly used for troubleshooting notes or additional setup instructions."
        ),
    )
    prereq: str | None = Field(
        None,
        description=(
            "A markdown string that included at the end of the auto generated "
            "`Prerequisites` section on the plugin page. Can be used to include custom "
            "prerequisites other than the default set."
        ),
    )


class ExtractorDetails(BasePluginDetails):
    """Extractor details model."""

    capabilities: list[enums.ExtractorCapabilityEnum]
    metadata: dict[str, t.Any] = Field(default_factory=dict)
    extractor_schema: dict[str, t.Any] | None = Field(None, alias="schema")
    select: list[str] = Field(default_factory=list)


class LoaderDetails(BasePluginDetails):
    """Loader details model."""

    capabilities: list[enums.LoaderCapabilityEnum]


class UtilityDetails(BasePluginDetails):
    """Utility details model."""

    pass


class OrchestrationDetails(BasePluginDetails):
    """Orchestration details model."""

    pass


class TransformDetails(BasePluginDetails):
    """Transform details model."""

    pass


class TransformerDetails(BasePluginDetails):
    """Transformer details model."""

    pass


class MapperDetails(BasePluginDetails):
    """Mapper details model."""

    pass


class FileDetails(BasePluginDetails):
    """File details model."""

    pass


type PluginDetails = (
    ExtractorDetails
    | LoaderDetails
    | UtilityDetails
    | OrchestrationDetails
    | TransformDetails
    | TransformerDetails
    | MapperDetails
    | FileDetails
)
