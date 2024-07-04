from __future__ import annotations

import enum

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, relationship

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./plugins.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

EntityBase = declarative_base()


class PluginType(str, enum.Enum):
    """Plugin types."""

    EXTRACTORS = "extractors"
    LOADERS = "loaders"
    TRANSFORMERS = "transformers"
    UTILITIES = "utilities"
    TRANSFORMS = "transforms"
    ORCHESTRATORS = "orchestrators"
    MAPPERS = "mappers"
    FILES = "files"


class Plugin(EntityBase):
    __tablename__ = "plugins"

    id = sa.Column(sa.String, primary_key=True)
    default_variant_id = sa.Column(sa.String, nullable=False)

    plugin_type = sa.Column(sa.Enum(PluginType), nullable=False)
    name = sa.Column(sa.String, nullable=False)

    default_variant = relationship("PluginVariant", uselist=False)
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

    id = sa.Column(sa.String, primary_key=True)
    plugin_id = sa.Column(sa.String, nullable=False)

    name = sa.Column(sa.String, nullable=False)
    pip_url = sa.Column(sa.String)
    repo = sa.Column(sa.String)
    namespace = sa.Column(sa.String, nullable=False)

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

    id = sa.Column(sa.String, primary_key=True)
    variant_id = sa.Column(sa.String, nullable=False)

    name = sa.Column(sa.String, nullable=False)
    label = sa.Column(sa.String)
    description = sa.Column(sa.String)
    kind = sa.Column(sa.String)
    value = sa.Column(sa.JSON, nullable=False)
    options = sa.Column(sa.JSON, nullable=True)


class Capability(EntityBase):
    __tablename__ = "capabilities"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["plugin_variants.id"],
        ),
    )

    id = sa.Column(sa.String, primary_key=True)
    variant_id = sa.Column(sa.String, nullable=False)

    name = sa.Column(sa.String, nullable=False)


class Keyword(EntityBase):
    __tablename__ = "keywords"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["plugin_variants.id"],
        ),
    )

    id = sa.Column(sa.String, primary_key=True)
    variant_id = sa.Column(sa.String, nullable=False)

    name = sa.Column(sa.String, nullable=False)
