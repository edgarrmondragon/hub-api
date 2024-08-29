from __future__ import annotations

import enum
import typing as t

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./plugins.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


class EntityBase(AsyncAttrs, DeclarativeBase):
    """Base entity class."""


class PluginType(enum.StrEnum):
    """Plugin types."""

    extractors = enum.auto()
    loaders = enum.auto()
    transformers = enum.auto()
    utilities = enum.auto()
    transforms = enum.auto()
    orchestrators = enum.auto()
    mappers = enum.auto()
    files = enum.auto()


class MaintenanceStatus(enum.StrEnum):
    """Maintenance statuses."""

    active = enum.auto()
    beta = enum.auto()
    development = enum.auto()
    inactive = enum.auto()
    unknown = enum.auto()


class Quality(enum.StrEnum):
    """Quality levels."""

    gold = enum.auto()
    silver = enum.auto()
    bronze = enum.auto()
    unknown = enum.auto()


class Plugin(EntityBase):
    __tablename__ = "plugins"

    id: Mapped[str] = mapped_column(primary_key=True)

    # TODO: Make this a foreign key?
    default_variant_id: Mapped[str]

    plugin_type: Mapped[PluginType]
    name: Mapped[str]

    variants: Mapped[list[PluginVariant]] = relationship(back_populates="plugin")


class PluginVariant(EntityBase):
    __tablename__ = "plugin_variants"

    id: Mapped[str] = mapped_column(primary_key=True)
    plugin_id: Mapped[str] = mapped_column(sa.ForeignKey("plugins.id"), index=True)

    name: Mapped[str]
    description: Mapped[str | None]
    docs: Mapped[str | None]
    logo_url: Mapped[str | None]
    pip_url: Mapped[str | None]
    repo: Mapped[str | None]
    namespace: Mapped[str]
    label: Mapped[str | None]
    hidden: Mapped[bool | None]

    maintenance_status: Mapped[MaintenanceStatus | None]
    quality: Mapped[Quality | None]
    domain_url: Mapped[str | None]
    definition: Mapped[str | None]
    next_steps: Mapped[str | None]
    settings_preamble: Mapped[str | None]
    usage: Mapped[str | None]
    prereq: Mapped[str | None]

    plugin: Mapped[Plugin] = relationship(back_populates="variants")
    settings: Mapped[list[Setting]] = relationship(back_populates="variant")
    capabilities: Mapped[list[Capability]] = relationship(back_populates="variant")
    keywords: Mapped[list[Keyword]] = relationship(back_populates="variant")
    select: Mapped[list[Select]] = relationship(back_populates="variant")


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
    kind: Mapped[str | None]
    value: Mapped[t.Any | None] = mapped_column(sa.JSON)
    options: Mapped[list[str] | None] = mapped_column(sa.JSON)
    sensitive: Mapped[bool | None]

    variant: Mapped[PluginVariant] = relationship(back_populates="settings")


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

    args: Mapped[str]
    description: Mapped[str | None]
    executable: Mapped[str | None]


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
