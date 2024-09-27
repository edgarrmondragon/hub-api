from __future__ import annotations

import os
import typing as t

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

from hub_api import enums  # noqa: TCH001

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL", "sqlite+aiosqlite:///./plugins.db")

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


class EntityBase(AsyncAttrs, DeclarativeBase):
    """Base entity class."""


class Plugin(EntityBase):
    __tablename__ = "plugins"

    id: Mapped[str] = mapped_column(primary_key=True)

    # TODO: Make this a foreign key?
    default_variant_id: Mapped[str]

    plugin_type: Mapped[enums.PluginTypeEnum]
    name: Mapped[str]

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
    capabilities: Mapped[list[Capability]] = relationship(back_populates="variant")
    keywords: Mapped[list[Keyword]] = relationship(back_populates="variant")
    commands: Mapped[list[Command]] = relationship(back_populates="variant")
    required_settings: Mapped[list[RequiredSetting]] = relationship(
        back_populates="variant",
    )

    # Extractor-specific
    select: Mapped[list[Select]] = relationship(back_populates="variant")
    extractor_metadata: Mapped[list[Metadata]] = relationship(back_populates="variant")

    maintainer: Mapped[Maintainer] = relationship(back_populates="plugins")


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
    env: Mapped[str | None]
    kind: Mapped[str | None]
    value: Mapped[t.Any | None] = mapped_column(sa.JSON)
    options: Mapped[list[dict[str, t.Any]] | None] = mapped_column(sa.JSON)
    sensitive: Mapped[bool | None]

    variant: Mapped[PluginVariant] = relationship(back_populates="settings")
    aliases: Mapped[list[SettingAlias]] = relationship(back_populates="setting", lazy="joined")


class SettingAlias(EntityBase):
    __tablename__ = "setting_aliases"

    id: Mapped[str] = mapped_column(primary_key=True)
    setting_id: Mapped[str] = mapped_column(
        sa.ForeignKey("settings.id"),
        index=True,
    )

    name: Mapped[str]
    setting: Mapped[Setting] = relationship(back_populates="aliases")


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

    variant: Mapped[PluginVariant] = relationship(back_populates="capabilities")


class Keyword(EntityBase):
    __tablename__ = "keywords"

    id: Mapped[str] = mapped_column(primary_key=True)
    variant_id: Mapped[str] = mapped_column(
        sa.ForeignKey("plugin_variants.id"),
        index=True,
    )

    name: Mapped[str]

    variant: Mapped[PluginVariant] = relationship(back_populates="keywords")


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

    variant: Mapped[PluginVariant] = relationship(back_populates="commands")


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

    variant: Mapped[PluginVariant] = relationship(back_populates="select")


class Metadata(EntityBase):
    __tablename__ = "metadata"

    id: Mapped[str] = mapped_column(primary_key=True)
    variant_id: Mapped[str] = mapped_column(
        sa.ForeignKey("plugin_variants.id"),
        index=True,
    )

    key: Mapped[str]
    value: Mapped[dict[str, t.Any]] = mapped_column(sa.JSON)

    variant: Mapped[PluginVariant] = relationship(back_populates="extractor_metadata")


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
