"""ETag implementation.

This combination of FastAPI middleware and dependency will add an ETag header to all responses.
The ETag value is the version of the hub-api package. The incoming request's If-None-Match
header is compared to the ETag value. If they match, a 304 Not Modified response is returned.
Otherwise, the response is returned as normal.

https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/ETag
"""  # noqa: I002

import functools
import http
import os
import textwrap
import typing as t
import uuid
from collections.abc import Awaitable, Callable

import fastapi.middleware
from fastapi import Header, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


@functools.lru_cache
def get_etag() -> str:
    """Get ETag value."""
    return os.environ.get("ETAG", f"etag-{uuid.uuid4()}")


class ETagMiddleware(BaseHTTPMiddleware):
    """ETag middleware."""

    @t.override
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> fastapi.Response:
        """Add ETag header to response."""
        response = await call_next(request)
        response.headers["ETag"] = get_etag()
        return response


def check_etag(
    if_none_match: t.Annotated[
        str | None,
        Header(
            description=textwrap.dedent("""\
                The `If-None-Match` HTTP request header makes the request conditional. \
                For `GET` and `HEAD` methods, the server will return the requested resource, \
                with a `200` status, only if it doesn't have an `ETag` matching the given ones. \
                For other methods, the request will be processed only if the eventually existing \
                resource's `ETag` doesn't match any of the values listed.

                https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-None-Match
            """),
            pattern=r"^etag-[A-Za-z0-9-]+$",
        ),
    ] = None,
) -> None:
    """Get ETag value."""
    if if_none_match == get_etag():
        raise fastapi.HTTPException(status_code=http.HTTPStatus.NOT_MODIFIED)
