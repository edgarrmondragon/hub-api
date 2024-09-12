"""API v1."""

from __future__ import annotations

import fastapi

from . import endpoints

router = fastapi.APIRouter()
router.include_router(endpoints.plugins.router, prefix="/plugins", tags=["plugins"])
router.include_router(endpoints.maintainers.router, prefix="/maintainers", tags=["maintainers"])

__all__ = ["router"]
