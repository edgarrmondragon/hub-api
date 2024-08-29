"""Hub API."""

from __future__ import annotations

import fastapi
from fastapi import responses, staticfiles
from fastapi.middleware import gzip

from . import api, crud

app = fastapi.FastAPI()
app.add_middleware(gzip.GZipMiddleware, minimum_size=1000)


@app.exception_handler(crud.NotFoundError)
def missing_variant_exception_handler(
    request: fastapi.Request,  # noqa: ARG001
    exc: crud.NotFoundError,
) -> responses.JSONResponse:
    return responses.JSONResponse(
        status_code=404,
        content={
            "detail": exc.args[0],
        },
    )


app.include_router(api.v1.api.router, prefix="/meltano/api/v1")
app.mount("/assets", staticfiles.StaticFiles(directory="static/assets"), name="assets")
