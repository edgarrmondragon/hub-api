"""Hub API."""

from __future__ import annotations

import http
from importlib import metadata

import fastapi
from fastapi import responses, staticfiles
from fastapi.middleware import gzip

from hub_api import api, exceptions, helpers

app = fastapi.FastAPI(
    version=metadata.version("hub-api"),
    dependencies=[fastapi.Depends(helpers.etag.check_etag)],
)
app.add_middleware(gzip.GZipMiddleware, minimum_size=1000)
app.add_middleware(helpers.etag.ETagMiddleware)


@app.exception_handler(exceptions.NotFoundError)
def missing_variant_exception_handler(
    request: fastapi.Request,  # noqa: ARG001
    exc: crud.NotFoundError,
) -> responses.JSONResponse:
    return responses.JSONResponse(
        status_code=http.HTTPStatus.NOT_FOUND,
        content={
            "detail": exc.args[0],
        },
    )


app.include_router(api.v1.api.router, prefix="/meltano/api/v1")
app.mount("/assets", staticfiles.StaticFiles(directory="static/assets"), name="assets")
