"""API v1."""
from __future__ import annotations

from fastapi import APIRouter

from .endpoints import plugins

router = APIRouter()
router.include_router(plugins.router, prefix="/plugins")
