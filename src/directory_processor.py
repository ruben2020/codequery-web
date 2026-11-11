#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
# SPDX-License-Identifier: MIT
#

from pathlib import Path
from typing import Any
from flask import abort
from .validator import get_base_dir, PathValidator


def get_folder_breadcrumbs(rel_path: str) -> list[dict[str, str]]:
    """
    Given a relative directory path (e.g. 'cli' or 'gui/dialogs'), returns a list of
    dicts with 'name' and 'path' for each folder segment.
    """
    clean = rel_path.replace("\\", "/").strip("/")
    if not clean:
        return []
    parts = clean.split("/")
    breadcrumbs = []
    accum = []
    for part in parts:
        if not part:
            continue
        accum.append(part)
        breadcrumbs.append({
            "name": part,
            "path": "/".join(accum),
        })
    return breadcrumbs


class DirectoryProcessor(PathValidator):
    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.abs_path: Path = self.safe_path(rel_path)

        if not self.abs_path.exists():
            abort(404)
        if not self.abs_path.is_dir():
            abort(400, "Requested path is not a directory")

    def get_contents(self) -> list[dict[str, Any]]:
        items = []
        base_dir = get_base_dir()

        for item in self.abs_path.iterdir():
            rel_item = item.relative_to(base_dir)

            items.append(
                {
                    "name": item.name,
                    "rel_path": rel_item.as_posix(),  # Ensures web-friendly '/' slashes
                    "is_dir": item.is_dir(),
                }
            )

        # Folders first, then files alphabetically
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        return items

    def get_parent_path(self) -> str | None:
        """Returns relative parent string or None if already at root."""
        base_dir = get_base_dir()
        if not self.rel_path or self.abs_path == base_dir:
            return None

        parent = self.abs_path.parent
        if parent == base_dir:
            return ""

        return parent.relative_to(base_dir).as_posix()
