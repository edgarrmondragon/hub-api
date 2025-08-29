"""Helper functions for the app."""

from __future__ import annotations

import contextlib
import re

import packaging.version
from starlette.requests import Request  # noqa: TC002

USER_AGENT_PATTERN = re.compile(r"^Meltano/(?P<version>[a-z0-9.]+)$")


def get_client_version(request: Request) -> packaging.version.Version | None:
    """Extract the Meltano version from the User-Agent header."""
    if (ua := request.headers.get("User-Agent")) and (match := USER_AGENT_PATTERN.match(ua)):
        with contextlib.suppress(packaging.version.InvalidVersion):
            return packaging.version.Version(match.group("version"))
    return None
