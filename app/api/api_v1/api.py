"""API v1."""

from fastapi import APIRouter

from .endpoints import plugins

router = APIRouter()
router.include_router(plugins.router, prefix="/plugins")
