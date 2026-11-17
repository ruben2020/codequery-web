#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
# SPDX-License-Identifier: MIT
#

from pathlib import Path
import subprocess
from typing import TypedDict
from flask import abort
from .validator import PathValidator, get_base_dir
from .highlighter import highlight_code, SymbolSearchHtmlFormatter


class FileData(TypedDict):
    content: str
    filename: str
    lang: str
    highlighted_content: str
    pygments_css: str


class FileProcessor(PathValidator):
    def __init__(self, rel_path: str, theme: str = "dark") -> None:
        self.rel_path = rel_path
        self.theme = theme if theme in ("light", "dark") else "dark"
        self.abs_path: Path = self.safe_path(rel_path)

        if not self.abs_path.exists():
            abort(404)
        if not self.abs_path.is_file():
            abort(400, "Requested path is not a file")

    def _detect_language(self) -> str:
        """
        Maps file extensions to standard Pygments language classes.
        Target languages: C/C++, Python, JavaScript, Go, Java, C#, Markdown
        """
        ext = self.abs_path.suffix.lower()
        name = self.abs_path.name.lower()

        if name == "cmakelists.txt":
            return "cmake"

        match ext:
            # C and C++
            case ".c":
                return "c"
            case ".cpp" | ".hpp" | ".cc" | ".cxx" | ".h" | ".hh" | ".hxx":
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

            # Markdown
            case ".md" | ".markdown":
                return "markdown"

            # CMake
            case ".cmake":
                return "cmake"

            # Fallback
            case _:
                return "plaintext"

    def get_raw_content(self) -> str:
        try:
            with open(self.abs_path, "r", encoding="utf-8", errors="replace", newline="") as f:
                return f.read()
        except Exception as e:
            abort(500, f"Error reading file: {str(e)}")

    def get_file_data(self, theme: str | None = None) -> FileData:
        try:
            active_theme = theme if theme in ("light", "dark") else self.theme
            style = "github-light" if active_theme == "light" else "github-dark"
            content = self.abs_path.read_text(encoding="utf-8", errors="replace")
            lang = self._detect_language()
            highlighted_content, pygments_css = highlight_code(
                content, filename=self.abs_path.name, lang=lang, style=style
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

    def get_git_history(self) -> str:
        base_dir = get_base_dir()
        try:
            rel_file = self.abs_path.relative_to(base_dir).as_posix()
        except ValueError:
            rel_file = self.rel_path.replace("\\", "/").lstrip("/")

        cmd = ["git", "log", "--", rel_file]
        try:
            res = subprocess.run(
                cmd,
                cwd=str(base_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if res.returncode == 0:
                return res.stdout
            return res.stdout or res.stderr
        except Exception as e:
            abort(500, f"Error running git log: {str(e)}")
