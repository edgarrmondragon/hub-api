"""Test files helper functions."""

from __future__ import annotations

import typing as t
from pathlib import Path

from hub_api.helpers import files

if t.TYPE_CHECKING:
    import pytest


def test_get_files_default() -> None:
    """Test get_files."""
    files.get_files.cache_clear()
    assert files.get_files() == Path("./plugin_files")


def test_get_files_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_files."""
    files.get_files.cache_clear()
    monkeypatch.setenv("PLUGINS_FILES_PATH", "/tmp")  # noqa: S108
    assert files.get_files() == Path("/tmp")  # noqa: S108


def test_get_files_cache() -> None:
    """Test get_files."""
    files.get_files.cache_clear()
    first_call = files.get_files()
    second_call = files.get_files()

    assert files.get_files() == Path("./plugin_files")
    assert files.get_files() is not Path("./plugin_files")
    assert first_call is second_call
