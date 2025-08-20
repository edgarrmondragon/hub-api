from __future__ import annotations

from typing import NamedTuple

from hub_api import enums, exceptions


class InvalidPluginTypeError(exceptions.BadParameterError):
    """Invalid plugin type error."""

    def __init__(self, *, plugin_type: str) -> None:
        super().__init__(f"'{plugin_type}' is not a valid plugin type")


class PluginID(NamedTuple):
    """Plugin ID."""

    plugin_type: enums.PluginTypeEnum
    plugin_name: str

    def as_db_id(self) -> str:
        return f"{self.plugin_type.value}.{self.plugin_name}"

    @classmethod
    def from_params(cls, *, plugin_type: str, plugin_name: str) -> PluginID:
        """Create a plugin ID from parameters.

        Args:
            plugin_type: Plugin type.
            plugin_name: Plugin name.

        Returns:
            Plugin ID.
        """
        try:
            plugin_type_member = enums.PluginTypeEnum(plugin_type)
        except ValueError:
            raise InvalidPluginTypeError(plugin_type=plugin_type) from None

        return cls(plugin_type=plugin_type_member, plugin_name=plugin_name)


class VariantID(NamedTuple):
    """Variant ID."""

    plugin_type: enums.PluginTypeEnum
    plugin_name: str
    plugin_variant: str

    def as_db_id(self) -> str:
        return f"{self.plugin_type.value}.{self.plugin_name}.{self.plugin_variant}"

    @classmethod
    def from_params(cls, *, plugin_type: str, plugin_name: str, plugin_variant: str) -> VariantID:
        """Create a variant ID from parameters.

        Args:
            plugin_type: Plugin type.
            plugin_name: Plugin name.
            plugin_variant: Plugin variant.

        Returns:
            Variant ID.
        """
        try:
            plugin_type_member = enums.PluginTypeEnum(plugin_type)
        except ValueError:
            raise InvalidPluginTypeError(plugin_type=plugin_type) from None

        return cls(plugin_type=plugin_type_member, plugin_name=plugin_name, plugin_variant=plugin_variant)
