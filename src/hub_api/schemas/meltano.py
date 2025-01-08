from __future__ import annotations

import typing as t

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Discriminator, Field, HttpUrl, RootModel, Tag

from hub_api import enums  # noqa: TC001


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(from_attributes=True)


# TODO: make this generic on the type of the setting value
class _BasePluginSetting(BaseModel):
    """Plugin setting model."""

    aliases: list[str] | None = None
    description: str | None = Field(
        None,
        description="The setting description.",
        examples=["The API token."],
    )
    documentation: str | None = Field(
        None,
        description="A URL to the documentation for this setting.",
        examples=["https://example.com/docs"],
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
    placeholder: str | None = Field(
        None,
        description="The setting placeholder.",
        examples=["my-api-token"],
    )
    sensitive: bool | None = Field(
        None,
        description="Whether the setting is sensitive.",
    )
    value: str | dict[str, t.Any] | list[t.Any] | bool | int | None = Field(None, description="The setting value.")


class StringSetting(_BasePluginSetting):
    """String setting model."""

    kind: t.Literal["string"] | None = None


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

    value: t.Any = Field(description="The option value")
    label: str | None = Field(None, description="The option label")


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


def _kind_discriminator(setting: dict[str, t.Any] | _BasePluginSetting) -> str:
    if isinstance(setting, dict):
        return setting.get("kind") or "string"  # pragma: no cover
    return getattr(setting, "kind", None) or "string"


class PluginSetting(RootModel[_BasePluginSetting]):
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


class Plugin(BaseModel):
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
    executable: str | None = Field(
        None,
        description="The plugin's executable name, as defined in setup.py (if a Python based plugin)",
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


class Extractor(Plugin, extra="forbid"):
    """Extractor details model."""

    capabilities: list[enums.ExtractorCapabilityEnum]
    metadata: dict[str, t.Any] = Field(default_factory=dict)
    extractor_schema: dict[str, t.Any] | None = Field(None, alias="schema")
    select: list[str] = Field(default_factory=list)


class Loader(Plugin, extra="forbid"):
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


class Utility(Plugin, extra="forbid"):
    """Utility details model."""

    pass


class Orchestrator(Plugin, extra="forbid"):
    """Orchestration details model."""

    pass


class Transform(Plugin, extra="forbid"):
    """Transform details model."""

    vars: dict[str, t.Any] = Field(default_factory=dict)


class Transformer(Plugin, extra="forbid"):
    """Transformer details model."""

    pass


class Mapper(Plugin, extra="forbid"):
    """Mapper details model."""

    capabilities: list[enums.MapperCapabilityEnum]


class File(Plugin, extra="forbid"):
    """File details model."""

    update: dict[str, bool] = Field(default_factory=dict)
