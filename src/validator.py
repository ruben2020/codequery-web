#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
# SPDX-License-Identifier: MIT
#

import os
from pathlib import Path
from flask import abort

# Resolves to absolute Path object pointing to target 'share' folder
BASE_DIR = Path(os.environ.get("CODEQUERY_SHARE_DIR", "./share")).resolve()


def get_base_dir() -> Path:
    """Returns the current BASE_DIR Path object."""
    global BASE_DIR
    return BASE_DIR


def set_base_dir(path: str | Path) -> Path:
    """Updates the BASE_DIR Path object to the specified directory."""
    global BASE_DIR
    BASE_DIR = Path(path).resolve()
    return BASE_DIR


class PathValidator:
    """Provides path verification boundaries for filesystem handlers."""

    @staticmethod
    def safe_path(relative_path: str) -> Path:
        """Resolves relative string path into a safe Path object inside BASE_DIR."""
        base_dir = get_base_dir()
        if not relative_path:
            return base_dir

        # Strip leading slashes to prevent absolute path override behavior
        clean_rel = relative_path.lstrip("/\\")
        resolved_path = (base_dir / clean_rel).resolve()

        # Modern Python traversal check
        if not resolved_path.is_relative_to(base_dir):
            abort(403)  # HTTP Forbidden

        return resolved_path
