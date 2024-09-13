"""Response schemas for the API."""

from __future__ import annotations

import typing as t

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Discriminator, Field, HttpUrl, RootModel, Tag

from hub_api import enums


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(from_attributes=True)


class Maintainer(BaseModel):
    """Maintainer model."""

    id: str = Field(description="The maintainer identifier", examples=["meltano"])
    label: str | None = Field(description="The maintainer label", examples=["Meltano"])
    url: HttpUrl | None = Field(description="The maintainer URL", examples=["https://meltano.com"])


class MaintainerPluginCount(BaseModel):
    """Maintainer model."""

    id: str = Field(description="The maintainer identifier", examples=["meltano"])
    label: str | None = Field(description="The maintainer label", examples=["Meltano"])
    url: HttpUrl | None = Field(description="The maintainer URL", examples=["https://meltano.com"])
    plugin_count: int = Field(description="The number of plugins the maintainer maintains", examples=[10])


class MaintainerDetails(BaseModel):
    """Maintainer details model."""

    id: str = Field(description="The maintainer identifier", examples=["meltano"])
    label: str | None = Field(description="The maintainer label", examples=["Meltano"])
    url: HttpUrl | None = Field(description="The maintainer URL", examples=["https://meltano.com"])
    links: dict[str, HttpUrl] = Field(description="Links to the maintainer's plugins", default_factory=dict)


class VariantReference(BaseModel):
    """Variant reference model."""

    ref: HttpUrl = Field(
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


_T = t.TypeVar("_T")


class _BasePluginSetting(BaseModel, t.Generic[_T]):
    """Plugin setting model."""

    aliases: list[str] | None = None
    description: str | None = Field(
        None,
        description="The setting description.",
        examples=["The API token."],
    )
    env: str | None = Field(None, description="The environment variable name.")
    label: str | None = Field(
        None,
        description="The setting label.",
        examples=["API Token"],
    )
    name: str = Field(
        description="The setting name.",
        json_schema_extra={"example": "token"},
    )
    sensitive: bool | None = Field(
        None,
        description="Whether the setting is sensitive.",
    )
    value: _T | None = Field(None, description="The setting value.")


class StringSetting(_BasePluginSetting[str]):
    """String setting model."""

    kind: t.Literal["string"] | None = None


class IntegerSetting(_BasePluginSetting[int]):
    """Integer setting model."""

    kind: t.Literal["integer"]


class BooleanSetting(_BasePluginSetting[bool]):
    """Boolean setting model."""

    kind: t.Literal["boolean"]


class DateIso8601Setting(_BasePluginSetting[str]):
    """Date ISO8601 setting model."""

    kind: t.Literal["date_iso8601"]


class EmailSetting(_BasePluginSetting[str]):
    """Email setting model."""

    kind: t.Literal["email"]


class PasswordSetting(_BasePluginSetting[str]):
    """Password setting model."""

    kind: t.Literal["password"]


class OAuthSetting(_BasePluginSetting[str]):
    """OAuth setting model."""

    kind: t.Literal["oauth"]


class Option(BaseModel):
    """Option model."""

    value: str = Field(description="The option value")
    label: str | None = Field(None, description="The option label")


class OptionsSetting(_BasePluginSetting[str]):
    """Options setting model."""

    kind: t.Literal["options"]
    options: list[Option] = Field(
        description="The setting options",
        default_factory=list,
    )


class FileSetting(_BasePluginSetting[str]):
    """File setting model."""

    kind: t.Literal["file"]


class ArraySetting(_BasePluginSetting[list[t.Any]]):
    """Array setting model."""

    kind: t.Literal["array"]


class ObjectSetting(_BasePluginSetting[dict[str, t.Any]]):
    """Object setting model."""

    kind: t.Literal["object"]


class HiddenSetting(_BasePluginSetting[str]):
    """Hidden setting model."""

    kind: t.Literal["hidden"]


def _kind_discriminator(setting: dict[str, t.Any] | _BasePluginSetting[t.Any]) -> str:
    if isinstance(setting, dict):
        return setting.get("kind") or "string"  # pragma: no cover
    return getattr(setting, "kind", None) or "string"


class PluginSetting(RootModel[_BasePluginSetting[t.Any]]):
    root: t.Annotated[
        t.Annotated[StringSetting, Tag("string")]
        | t.Annotated[IntegerSetting, Tag("integer")]
        | t.Annotated[BooleanSetting, Tag("boolean")]
        | t.Annotated[DateIso8601Setting, Tag("date_iso8601")]
        | t.Annotated[EmailSetting, Tag("email")]
        | t.Annotated[PasswordSetting, Tag("password")]
        | t.Annotated[OAuthSetting, Tag("oauth")]
        | t.Annotated[OptionsSetting, Tag("options")]
        | t.Annotated[FileSetting, Tag("file")]
        | t.Annotated[ArraySetting, Tag("array")]
        | t.Annotated[ObjectSetting, Tag("object")]
        | t.Annotated[HiddenSetting, Tag("hidden")],
        Discriminator(_kind_discriminator),
    ]


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
    label: str | None = Field(None, description="The plugin label", examples=["CSV Tap"])
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
    pip_url: str | None = Field(
        None,
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
        None,
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

    keywords: list[str] = Field(
        default_factory=list,
        description="A list of keywords for the plugin",
    )
    maintenance_status: enums.MaintenanceStatusEnum | None = Field(
        None,
        description="The maintenance status of the plugin",
    )
    quality: enums.QualityEnum | None = Field(
        None,
        description="The quality of the plugin",
    )
    settings: list[PluginSetting] = Field(default_factory=list)
    commands: dict[str, str | Command] = Field(
        default_factory=dict,
        description=(
            "An object containing commands to be run by the plugin, the keys are the "
            "name of the command and the values are the arguments to be passed to the "
            "plugin executable."
        ),
    )
    requires: dict[enums.PluginTypeEnum, list[PluginRequires]] = Field(default_factory=dict)

    hidden: bool | None = Field(
        None,
        description="Whether the plugin should be shown when listing or not.",
    )

    domain_url: HttpUrl | None = Field(
        None,
        description="Links to the website representing the database, api, etc.",
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


class ExtractorDetails(BasePluginDetails, extra="forbid"):
    """Extractor details model."""

    capabilities: list[enums.ExtractorCapabilityEnum]
    metadata: dict[str, t.Any] = Field(default_factory=dict)
    extractor_schema: dict[str, t.Any] | None = Field(None, alias="schema")
    select: list[str] = Field(default_factory=list)


class LoaderDetails(BasePluginDetails, extra="forbid"):
    """Loader details model."""

    capabilities: list[enums.LoaderCapabilityEnum] = Field(default_factory=list)
    target_schema: str | None = Field(
        None,
        description="The target schema for the loader",
    )
    dialect: str | None = Field(
        None,
        description="The dialect for the loader",
        examples=["postgres"],
    )


class UtilityDetails(BasePluginDetails, extra="forbid"):
    """Utility details model."""

    pass


class OrchestrationDetails(BasePluginDetails, extra="forbid"):
    """Orchestration details model."""

    pass


class TransformDetails(BasePluginDetails, extra="forbid"):
    """Transform details model."""

    vars: dict[str, t.Any] = Field(default_factory=dict)


class TransformerDetails(BasePluginDetails, extra="forbid"):
    """Transformer details model."""

    pass


class MapperDetails(BasePluginDetails, extra="forbid"):
    """Mapper details model."""

    pass


class FileDetails(BasePluginDetails, extra="forbid"):
    """File details model."""

    update: dict[str, bool] = Field(default_factory=dict)


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
