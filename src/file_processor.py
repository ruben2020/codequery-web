#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

from pathlib import Path
from typing import TypedDict
from flask import abort
from .validator import PathValidator


class FileData(TypedDict):
    content: str
    filename: str
    lang: str


class FileProcessor(PathValidator):
    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.abs_path: Path = self.safe_path(rel_path)

        if not self.abs_path.exists():
            abort(404)
        if not self.abs_path.is_file():
            abort(400, "Requested path is not a file")

    def _detect_language(self) -> str:
        """
        Maps file extensions to standard Prism.js language classes.
        Target languages: C/C++, Python, JavaScript, Go, Java, C#
        """
        ext = self.abs_path.suffix.lower()

        match ext:
            # C and C++
            case ".c" | ".h":
                return "c"
            case ".cpp" | ".hpp" | ".cc" | ".cxx":
                return "cpp"

            # Python
            case ".py" | ".pyw":
                return "python"

            # JavaScript
            case ".js" | ".mjs" | ".cjs":
                return "javascript"

            # Go
            case ".go":
                return "go"

            # Java
            case ".java":
                return "java"

            # C#
            case ".cs":
                return "csharp"

            # Fallback
            case _:
                return "plaintext"

    def get_file_data(self) -> FileData:
        try:
            content = self.abs_path.read_text(encoding="utf-8", errors="replace")

            return {
                "content": content,
                "filename": self.abs_path.name,
                "lang": self._detect_language(),
            }
        except Exception as e:
            abort(500, f"Error reading file: {str(e)}")
