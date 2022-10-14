"""Test files helper functions."""

from pathlib import Path

from app.helpers.files import get_files


def test_get_files_default():
    """Test get_files."""
    get_files.cache_clear()
    assert get_files() == Path("./plugin_files")


def test_get_files_env(monkeypatch):
    """Test get_files."""
    get_files.cache_clear()
    monkeypatch.setenv("PLUGINS_FILES_PATH", "/tmp")
    assert get_files() == Path("/tmp")


def test_get_files_cache():
    """Test get_files."""
    get_files.cache_clear()
    first_call = get_files()
    second_call = get_files()

    assert get_files() == Path("./plugin_files")
    assert get_files() is not Path("./plugin_files")
    assert first_call is second_call
