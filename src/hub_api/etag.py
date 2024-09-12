"""ETag implementation.

This combination of FastAPI middleware and dependency will add an ETag header to all responses.
The ETag value is the version of the hub-api package. The incoming request's If-None-Match
header is compared to the ETag value. If they match, a 304 Not Modified response is returned.
Otherwise, the response is returned as normal.

https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/ETag
"""  # noqa: I002

import http
import typing as t
from importlib import metadata

import fastapi.middleware
from fastapi import Header, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


def get_etag() -> str:
    """Get ETag value."""
    return f"etag-{metadata.version("hub-api")}"


class ETagMiddleware(BaseHTTPMiddleware):
    """ETag middleware."""

    async def dispatch(  # noqa: PLR6301
        self,
        request: Request,
        call_next: t.Callable[[Request], t.Awaitable[Response]],
    ) -> fastapi.Response:
        """Add ETag header to response."""
        response = await call_next(request)
        response.headers["ETag"] = get_etag()
        return response


def check_etag(if_none_match: t.Annotated[str | None, Header()] = None) -> None:
    """Get ETag value."""
    if if_none_match == get_etag():
        raise fastapi.HTTPException(status_code=http.HTTPStatus.NOT_MODIFIED)
