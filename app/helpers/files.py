"""File helper functions."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


@lru_cache
def get_files() -> Path:
    """Get the plugin files.

    Returns:
        The plugin files path.
    """
    return Path(os.getenv("PLUGINS_FILES_PATH", "./plugin_files"))
