from __future__ import annotations

import enum

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./plugins.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


class EntityBase(DeclarativeBase):
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


class Plugin(EntityBase):
    __tablename__ = "plugins"

    id: Mapped[str] = mapped_column(primary_key=True)

    # TODO: Make this a foreign key
    default_variant_id: Mapped[str] = mapped_column(nullable=False)

    plugin_type: Mapped[PluginType] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)

    # default_variant: Mapped[PluginVariant] = relationship(
    #     "PluginVariant", uselist=False
    # )
    # variants = relationship("PluginVariant", backref="plugin")


class PluginVariant(EntityBase):
    __tablename__ = "plugin_variants"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["plugin_id"],
            ["plugins.id"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    plugin_id: Mapped[str] = mapped_column(nullable=False)

    name: Mapped[str] = mapped_column(nullable=False)
    pip_url: Mapped[str] = mapped_column()
    repo: Mapped[str] = mapped_column()
    namespace: Mapped[str] = mapped_column(nullable=False)
    hidden: Mapped[bool] = mapped_column()

    # plugin = relationship("Plugin", backref="variants")

    settings = relationship("Setting", backref="plugin")
    capabilities = relationship("Capability", backref="plugin")
    keywords = relationship("Keyword", backref="plugin")


class Setting(EntityBase):
    __tablename__ = "settings"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["plugin_variants.id"],
        ),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    variant_id: Mapped[str] = mapped_column(nullable=False)

    name: Mapped[str] = mapped_column(nullable=False)
    label: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    kind: Mapped[str] = mapped_column()
    value: Mapped[str] = mapped_column()
    options: Mapped[str] = mapped_column()
    sensitive: Mapped[bool] = mapped_column()


class Capability(EntityBase):
    __tablename__ = "capabilities"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["plugin_variants.id"],
        ),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    variant_id: Mapped[str] = mapped_column(nullable=False)

    name: Mapped[str] = mapped_column(nullable=False)


class Keyword(EntityBase):
    __tablename__ = "keywords"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["plugin_variants.id"],
        ),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    variant_id: Mapped[str] = mapped_column(nullable=False)

    name: Mapped[str] = mapped_column(nullable=False)
