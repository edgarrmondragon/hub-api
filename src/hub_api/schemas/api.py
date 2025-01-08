"""Pydantic models used to validate API responses."""

from __future__ import annotations

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field, HttpUrl

from hub_api import enums
from hub_api.schemas import meltano


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(from_attributes=True)


class _BaseMaintainerSchema(BaseModel):
    """Base maintainer schema."""

    id: str = Field(description="The maintainer identifier", examples=["meltano"])
    label: str | None = Field(description="The maintainer label", examples=["Meltano"])
    url: HttpUrl | None = Field(description="The maintainer URL", examples=["https://meltano.com"])


class Maintainer(_BaseMaintainerSchema):
    """Maintainer model."""

    class Links(BaseModel):
        """Maintainer links."""

        details: str = Field(description="Links to maintainer details")

    links: Links


class MaintainersList(BaseModel):
    maintainers: list[Maintainer]


class MaintainerPluginCount(_BaseMaintainerSchema):
    """Maintainer model."""

    plugin_count: int = Field(description="The number of plugins the maintainer maintains", examples=[10])


class MaintainerDetails(_BaseMaintainerSchema):
    """Maintainer details model."""

    links: dict[str, str] = Field(description="Links to the maintainer's plugins", default_factory=dict)


class VariantReference(BaseModel):
    """Variant reference model."""

    ref: HttpUrl = Field(
        description="API URL for the variant",
        examples=["https://hub.meltano.com/meltano/api/v1/plugins/extractors/tap-github--singer-io"],
    )


class PluginRef(BaseModel):
    """Plugin entry."""

    default_variant: str = Field(description="The default variant of the plugin", examples=["singer-io"])
    variants: dict[str, VariantReference] = Field(description="The variants of the plugin", default_factory=dict)
    logo_url: HttpUrl | None = Field(None, description="URL to the plugin's logo")


type PluginTypeIndex = dict[str, PluginRef]
type PluginIndex = dict[enums.PluginTypeEnum, PluginTypeIndex]


class PluginResponse(meltano.Plugin):
    """Plugin response model."""

    logo_url: HttpUrl | None = Field(None, description="URL to the plugin's logo")
    documentation: HttpUrl | None = Field(None, description="URL to the plugin's documentation")


class ExtractorResponse(PluginResponse, meltano.Extractor):
    """Extractor response model."""


class LoaderResponse(PluginResponse, meltano.Loader):
    """Loader response model."""


class UtilityResponse(PluginResponse, meltano.Utility):
    """Utility response model."""


class OrchestratorResponse(PluginResponse, meltano.Orchestrator):
    """Orchestrator response model."""


class TransformResponse(PluginResponse, meltano.Transform):
    """Transform response model."""


class TransformerResponse(PluginResponse, meltano.Transformer):
    """Transformer response model."""


class MapperResponse(PluginResponse, meltano.Mapper):
    """Mapper response model."""


class FileResponse(PluginResponse, meltano.File):
    """File response model."""
