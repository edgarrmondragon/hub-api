"""Hub API."""

from __future__ import annotations

import http
import textwrap
from importlib import metadata, resources

import fastapi
from fastapi import responses, staticfiles
from fastapi.middleware import gzip

from hub_api import api, exceptions, static
from hub_api.helpers import etag

app = fastapi.FastAPI(
    title="Meltano Hub API",
    description=textwrap.dedent("""\
        The Meltano Hub API provides access to Meltano's plugin registry. \
        It allows you to search for plugins, view their details, and download \
        the necessary files to install them. \

        - The API is versioned, with the current version being v1.
        - The API is read-only, and no authentication is required.
    """),
    version=metadata.version("hub-api"),
    dependencies=[fastapi.Depends(etag.check_etag)],
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Local development server",
        },
    ],
)
app.add_middleware(gzip.GZipMiddleware, minimum_size=1000)
app.add_middleware(etag.ETagMiddleware)
assets = resources.files(static) / "assets"


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


@app.exception_handler(exceptions.BadParameterError)
def bad_parameter_exception_handler(
    request: fastapi.Request,  # noqa: ARG001
    exc: exceptions.BadParameterError,
) -> responses.JSONResponse:
    return responses.JSONResponse(
        status_code=http.HTTPStatus.BAD_REQUEST,
        content={
            "detail": exc.args[0],
        },
    )


app.include_router(api.v1.api.router, prefix="/meltano/api/v1")
app.mount("/assets", staticfiles.StaticFiles(directory=assets), name="assets")  # type: ignore[arg-type]
