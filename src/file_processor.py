#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
# SPDX-License-Identifier: MIT
#

from pathlib import Path
from typing import TypedDict
from flask import abort
from .validator import PathValidator
from .highlighter import highlight_code, SymbolSearchHtmlFormatter


class FileData(TypedDict):
    content: str
    filename: str
    lang: str
    highlighted_content: str
    pygments_css: str


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
            lang = self._detect_language()
            highlighted_content, pygments_css = highlight_code(
                content, filename=self.abs_path.name, lang=lang
            )

            return {
                "content": content,
                "filename": self.abs_path.name,
                "lang": lang,
                "highlighted_content": highlighted_content,
                "pygments_css": pygments_css,
            }
        except Exception as e:
            abort(500, f"Error reading file: {str(e)}")
