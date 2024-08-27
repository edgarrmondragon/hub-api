"""Hub API."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from hub_api.api.api_v1.api import router as api_router
from hub_api.crud import PluginVariantNotFoundError

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.exception_handler(PluginVariantNotFoundError)
def missing_variant_exception_handler(
    request: Request,
    exc: PluginVariantNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "detail": exc.args[0],
        },
    )


app.include_router(api_router, prefix="/meltano/api/v1")
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
