#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
# SPDX-License-Identifier: MIT
#

from pathlib import Path
from flask import abort

# Resolves to absolute Path object pointing to target 'share' folder
BASE_DIR = Path("./share").resolve()


class PathValidator:
    """Provides path verification boundaries for filesystem handlers."""

    @staticmethod
    def safe_path(relative_path: str) -> Path:
        """Resolves relative string path into a safe Path object inside BASE_DIR."""
        if not relative_path:
            return BASE_DIR

        # Strip leading slashes to prevent absolute path override behavior
        clean_rel = relative_path.lstrip("/\\")
        resolved_path = (BASE_DIR / clean_rel).resolve()

        # Modern Python traversal check
        if not resolved_path.is_relative_to(BASE_DIR):
            abort(403)  # HTTP Forbidden

        return resolved_path
