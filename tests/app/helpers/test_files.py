"""Test files helper functions."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.helpers.files import get_files


def test_get_files_default() -> None:
    """Test get_files."""
    get_files.cache_clear()
    assert get_files() == Path("./plugin_files")


def test_get_files_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_files."""
    get_files.cache_clear()
    monkeypatch.setenv("PLUGINS_FILES_PATH", "/tmp")  # noqa: S108
    assert get_files() == Path("/tmp")  # noqa: S108


def test_get_files_cache() -> None:
    """Test get_files."""
    get_files.cache_clear()
    first_call = get_files()
    second_call = get_files()

    assert get_files() == Path("./plugin_files")
    assert get_files() is not Path("./plugin_files")
    assert first_call is second_call
