#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
# SPDX-License-Identifier: MIT
#

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List
from flask import url_for
from .validator import BASE_DIR


def resolve_relative_path(full_path: str) -> str:
    """
    Given a file path from cqsearch (e.g. $HOME/.../share/cli/main_cli.cpp),
    resolves it to a path relative to BASE_DIR (e.g. cli/main_cli.cpp).
    """
    expanded = os.path.expandvars(full_path)
    try:
        p = Path(expanded).resolve()
        if p.is_relative_to(BASE_DIR):
            return p.relative_to(BASE_DIR).as_posix()
    except Exception:
        pass

    normalized = full_path.replace("\\", "/")
    if "/share/" in normalized:
        return normalized.split("/share/", 1)[1]
    if normalized.startswith("share/"):
        return normalized[len("share/") :]
    return normalized.lstrip("/")


class SearchProcessor:
    def __init__(
        self,
        search_term: str,
        search_type: str = "1",
        path_filter: str = "",
        exact_match: bool = False,
    ) -> None:
        self.search_term = search_term.strip()
        self.search_type = str(search_type).strip() if search_type else "1"
        self.path_filter = path_filter.strip()
        self.exact_match = exact_match

    def execute(self) -> List[Dict[str, Any]]:
        if not self.search_term:
            return []

        cqsearch_bin = shutil.which("cqsearch") or "cqsearch"
        cmd = [
            cqsearch_bin,
            "-s",
            "cq.db",
            "-t",
            self.search_term,
            "-p",
            self.search_type,
            "-u",
        ]

        if self.path_filter:
            cmd.extend(["-b", self.path_filter])

        if self.exact_match:
            cmd.append("-e")
        else:
            cmd.append("-f")

        try:
            res = subprocess.run(
                cmd,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception:
            return []

        if res.returncode != 0:
            return []

        results: List[Dict[str, Any]] = []
        for line in res.stdout.splitlines():
            line = line.strip("\r\n")
            if not line:
                continue

            if self.search_type == "4":
                parts = line.split("\t", 1)
                path_with_line = parts[0]
                preview = parts[1] if len(parts) > 1 else ""
                symbol = ""
            else:
                parts = line.split("\t", 2)
                symbol = parts[0]
                path_with_line = parts[1] if len(parts) > 1 else ""
                preview = parts[2] if len(parts) > 2 else ""

            # Extract relative path and line number
            if ":" in path_with_line:
                full_file_path, line_no = path_with_line.rsplit(":", 1)
            else:
                full_file_path, line_no = path_with_line, ""

            rel_path = resolve_relative_path(full_file_path)
            try:
                file_url = url_for("view_file", p=rel_path)
            except RuntimeError:
                file_url = f"/openfile?p={rel_path}"

            if line_no:
                file_url += f"#line-{line_no}"

            results.append(
                {
                    "symbol": symbol,
                    "path_with_line": path_with_line,
                    "preview": preview,
                    "url": file_url,
                }
            )

        return results
