"""Hub API."""

from __future__ import annotations

import http
from importlib import metadata

import fastapi
from fastapi import responses, staticfiles
from fastapi.middleware import gzip

from hub_api import api, exceptions
from hub_api.helpers import etag

app = fastapi.FastAPI(
    version=metadata.version("hub-api"),
    dependencies=[fastapi.Depends(etag.check_etag)],
)
app.add_middleware(gzip.GZipMiddleware, minimum_size=1000)
app.add_middleware(etag.ETagMiddleware)


@app.exception_handler(exceptions.NotFoundError)
def not_found_exception_handler(
    request: fastapi.Request,  # noqa: ARG001
    exc: exceptions.NotFoundError,
) -> responses.JSONResponse:
    return responses.JSONResponse(
        status_code=http.HTTPStatus.NOT_FOUND,
        content={
            "detail": exc.args[0],
        },
    )


app.include_router(api.v1.api.router, prefix="/meltano/api/v1")
app.mount("/assets", staticfiles.StaticFiles(directory="static/assets"), name="assets")
