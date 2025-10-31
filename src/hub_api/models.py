from __future__ import annotations

import collections
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

from hub_api import enums  # noqa: TC001


class EntityBase(AsyncAttrs, DeclarativeBase):
    """Base entity class."""


class Plugin(EntityBase):
    __tablename__ = "plugins"

    id: Mapped[str] = mapped_column(primary_key=True)

    # TODO: Make this a foreign key?
    default_variant_id: Mapped[str]

    plugin_type: Mapped[enums.PluginTypeEnum]
    name: Mapped[str] = mapped_column(sa.String(63))

    variants: Mapped[list[PluginVariant]] = relationship(back_populates="plugin")


class PluginVariant(EntityBase):
    __tablename__ = "plugin_variants"

    id: Mapped[str] = mapped_column(primary_key=True)
    plugin_id: Mapped[str] = mapped_column(sa.ForeignKey("plugins.id"), index=True)

    name: Mapped[str] = mapped_column(sa.ForeignKey("maintainers.id"), index=True)
    description: Mapped[str | None]
    docs: Mapped[str | None]
    logo_url: Mapped[str | None]
    pip_url: Mapped[str | None]
    executable: Mapped[str | None]
    repo: Mapped[str | None]
    ext_repo: Mapped[str | None]
    namespace: Mapped[str]
    label: Mapped[str | None]
    hidden: Mapped[bool | None]

    maintenance_status: Mapped[enums.MaintenanceStatusEnum | None]
    quality: Mapped[enums.QualityEnum | None]
    domain_url: Mapped[str | None]
    definition: Mapped[str | None]
    next_steps: Mapped[str | None]
    settings_preamble: Mapped[str | None]
    usage: Mapped[str | None]
    prereq: Mapped[str | None]

    plugin: Mapped[Plugin] = relationship(back_populates="variants", lazy="joined")
    settings: Mapped[list[Setting]] = relationship(back_populates="variant")

    plugin_capabilities: Mapped[list[Capability]] = relationship(back_populates="variant", lazy="joined")
    plugin_commands: Mapped[list[Command]] = relationship(back_populates="variant", lazy="joined")
    plugin_keywords: Mapped[list[Keyword]] = relationship(back_populates="variant", lazy="joined")
    required_settings: Mapped[list[RequiredSetting]] = relationship(back_populates="variant", lazy="joined")

    # Extractor-specific
    select_expressions: Mapped[list[Select]] = relationship(back_populates="variant", lazy="joined")
    metadata_overrides: Mapped[list[Metadata]] = relationship(back_populates="variant", lazy="joined")

    maintainer: Mapped[Maintainer] = relationship(back_populates="plugins")

    @property
    def capabilities(self) -> list[str]:
        """The capabilities for the variant."""
        return [c.name for c in self.plugin_capabilities]

    @property
    def commands(self) -> dict[str, Command]:
        """The commands for the variant."""
        return {cmd.name: cmd for cmd in self.plugin_commands}

    @property
    def select(self) -> list[str] | None:
        """The select expressions for the variant."""
        return [s.expression for s in self.select_expressions] if self.select_expressions else None

    @property
    def extractor_metadata(self) -> dict[str, dict[str, Any]] | None:
        """The metadata for the variant."""
        return {m.key: m.value for m in self.metadata_overrides} if self.metadata_overrides else None

    @property
    def settings_group_validation(self) -> list[list[str]]:
        """The settings group validation for the variant."""
        settings_groups: dict[int, list[str]] = collections.defaultdict(list)
        for required in self.required_settings:
            settings_groups[required.group_id].append(required.setting_name)
        return list(settings_groups.values())


class Setting(EntityBase):
    __tablename__ = "settings"

    id: Mapped[str] = mapped_column(primary_key=True)
    variant_id: Mapped[str] = mapped_column(
        sa.ForeignKey("plugin_variants.id"),
        index=True,
    )

    name: Mapped[str]
    label: Mapped[str | None]
    description: Mapped[str | None]
    documentation: Mapped[str | None]
    placeholder: Mapped[str | None]
    env: Mapped[str | None]
    kind: Mapped[str | None]
    value: Mapped[Any | None] = mapped_column(sa.JSON)
    options: Mapped[list[dict[str, Any]] | None] = mapped_column(sa.JSON)
    sensitive: Mapped[bool | None]

    variant: Mapped[PluginVariant] = relationship(back_populates="settings")
    setting_aliases: Mapped[list[SettingAlias]] = relationship(back_populates="setting", lazy="joined")

    @property
    def aliases(self) -> list[str] | None:
        """The alias names for the setting."""
        return [alias.name for alias in self.setting_aliases] or None


class SettingAlias(EntityBase):
    __tablename__ = "setting_aliases"

    id: Mapped[str] = mapped_column(primary_key=True)
    setting_id: Mapped[str] = mapped_column(
        sa.ForeignKey("settings.id"),
        index=True,
    )

    name: Mapped[str]
    setting: Mapped[Setting] = relationship(back_populates="setting_aliases")


class RequiredSetting(EntityBase):
    __tablename__ = "setting_groups"
    __table_args__ = (
        sa.PrimaryKeyConstraint(
            "variant_id",
            "group_id",
            "setting_name",
        ),
    )

    variant_id: Mapped[str] = mapped_column(
        sa.ForeignKey("plugin_variants.id"),
        index=True,
    )
    setting_id: Mapped[str] = mapped_column(
        sa.ForeignKey("settings.id"),
        index=True,
    )

    group_id: Mapped[int]
    setting_name: Mapped[str]

    variant: Mapped[PluginVariant] = relationship(back_populates="required_settings")
    setting: Mapped[Setting | None] = relationship(lazy="joined")


class Capability(EntityBase):
    __tablename__ = "capabilities"

    variant_id: Mapped[str] = mapped_column(
        sa.ForeignKey("plugin_variants.id"),
        index=True,
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]

    variant: Mapped[PluginVariant] = relationship(back_populates="plugin_capabilities")


class Keyword(EntityBase):
    __tablename__ = "keywords"

    id: Mapped[str] = mapped_column(primary_key=True)
    variant_id: Mapped[str] = mapped_column(
        sa.ForeignKey("plugin_variants.id"),
        index=True,
    )

    name: Mapped[str]

    variant: Mapped[PluginVariant] = relationship(back_populates="plugin_keywords")


class Command(EntityBase):
    __tablename__ = "commands"

    id: Mapped[str] = mapped_column(primary_key=True)
    variant_id: Mapped[str] = mapped_column(
        sa.ForeignKey("plugin_variants.id"),
        index=True,
    )

    name: Mapped[str]
    args: Mapped[str]
    description: Mapped[str | None]
    executable: Mapped[str | None]

    variant: Mapped[PluginVariant] = relationship(back_populates="plugin_commands")


class PluginRequires(EntityBase):
    __tablename__ = "plugin_requires"

    id: Mapped[str] = mapped_column(primary_key=True)
    variant_id: Mapped[str] = mapped_column(
        sa.ForeignKey("plugin_variants.id"),
        index=True,
    )

    name: Mapped[str]
    variant: Mapped[str]


class Select(EntityBase):
    __tablename__ = "selects"

    id: Mapped[str] = mapped_column(primary_key=True)
    variant_id: Mapped[str] = mapped_column(
        sa.ForeignKey("plugin_variants.id"),
        index=True,
    )

    expression: Mapped[str]

    variant: Mapped[PluginVariant] = relationship(back_populates="select_expressions")


class Metadata(EntityBase):
    __tablename__ = "metadata"

    id: Mapped[str] = mapped_column(primary_key=True)
    variant_id: Mapped[str] = mapped_column(
        sa.ForeignKey("plugin_variants.id"),
        index=True,
    )

    key: Mapped[str]
    value: Mapped[dict[str, Any]] = mapped_column(sa.JSON)

    variant: Mapped[PluginVariant] = relationship(back_populates="metadata_overrides")


class Maintainer(EntityBase):
    __tablename__ = "maintainers"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str | None]
    label: Mapped[str | None]
    url: Mapped[str | None]

    plugins: Mapped[list[PluginVariant]] = relationship(back_populates="maintainer")

    @property
    def links(self) -> dict[str, str]:
        """Maintainer links."""
        return {
            "details": f"/meltano/v1/maintainers/{self.id}",
        }
