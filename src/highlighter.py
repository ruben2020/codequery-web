#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
# SPDX-License-Identifier: MIT
#

import urllib.parse
from typing import Tuple
import pygments.styles
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import (
    TextLexer,
    get_lexer_by_name,
    get_lexer_for_filename,
)
from pygments.style import Style
from pygments.styles._mapping import STYLES
from pygments.token import (
    Comment,
    Error,
    Generic,
    Keyword,
    Literal,
    Name,
    Number,
    Operator,
    String,
    Text,
    Token,
)
from pygments.util import ClassNotFound


class GhLightStyle(Style):
    """
    GitHub's Light-Colorscheme based theme for Pygments.
    """

    name = "github-light"

    background_color = "#ffffff"
    highlight_color = "#fff8c5"

    line_number_special_color = "#1f2328"
    line_number_special_background_color = "#fff8c5"

    line_number_color = "#6e7781"
    line_number_background_color = "#ffffff"

    styles = {
        Token: "#1f2328",
        Error: "#cf222e",
        Keyword: "#cf222e",
        Keyword.Constant: "#0550ae",
        Keyword.Pseudo: "#0550ae",
        Name: "#1f2328",
        Name.Class: "bold #953800",
        Name.Constant: "bold #0550ae",
        Name.Decorator: "bold #8250df",
        Name.Entity: "#953800",
        Name.Exception: "bold #953800",
        Name.Function: "bold #8250df",
        Name.Label: "bold #0550ae",
        Name.Namespace: "#cf222e",
        Name.Property: "#0550ae",
        Name.Tag: "#116329",
        Name.Variable: "#0550ae",
        Literal: "#0a3069",
        Literal.Date: "#0550ae",
        String: "#0a3069",
        String.Affix: "#0550ae",
        String.Delimiter: "#0550ae",
        String.Escape: "#0550ae",
        String.Heredoc: "#0550ae",
        String.Regex: "#0550ae",
        Number: "#0550ae",
        Comment: "italic #57606a",
        Comment.Preproc: "bold #57606a",
        Comment.Special: "bold italic #57606a",
        Operator: "bold #cf222e",
        Generic: "#1f2328",
        Generic.Deleted: "bg:#ffebe9 #82071e",
        Generic.Emph: "italic",
        Generic.Error: "#82071e",
        Generic.Heading: "bold #0550ae",
        Generic.Inserted: "bg:#dafbe1 #116329",
        Generic.Output: "#57606a",
        Generic.Prompt: "#57606a",
        Generic.Strong: "bold",
        Generic.EmphStrong: "bold italic",
        Generic.Subheading: "#0550ae",
        Generic.Traceback: "#cf222e",
        Generic.Underline: "underline",
        Text.Whitespace: "#6e7781",
    }


STYLES["GhLightStyle"] = (__name__, "github-light", ())
pygments.styles.STYLE_MAP["github-light"] = f"{__name__.split('.')[-1]}::GhLightStyle"
pygments.styles._STYLE_NAME_TO_MODULE_MAP["github-light"] = (__name__, "GhLightStyle")


class SymbolSearchHtmlFormatter(HtmlFormatter):
    """
    Pygments HTML Formatter that wraps every symbol (Token.Name and subtypes)
    in a search hyperlink pointing to a search endpoint.
    """

    def __init__(
        self,
        search_url_prefix: str = "/search_results?search_term=",
        **options,
    ) -> None:
        super().__init__(**options)
        self.search_url_prefix = search_url_prefix

    def _format_lines(self, tokensource):
        span_openers = self.span_element_openers
        translate = self._translate_parts
        lsep = self.lineseparator
        nocls = self.noclasses
        lspan = ""
        line = []

        for ttype, value in tokensource:
            try:
                cspan = span_openers[ttype]
            except KeyError:
                title = f' title="{".".join(ttype)}"' if self.debug_token_types else ""
                if nocls:
                    css_style = self._get_css_inline_styles(ttype)
                    if css_style:
                        css_style = self.class2style[css_style][0]
                        cspan = f'<span style="{css_style}"{title}>'
                    else:
                        cspan = ""
                else:
                    css_class = self._get_css_classes(ttype)
                    cspan = f'<span class="{css_class}"{title}>' if css_class else ""
                span_openers[ttype] = cspan

            parts = list(translate(value))

            # Turn every symbol (identifier / Token.Name) into a search hyperlink
            if ttype in Token.Name:
                term = value.strip()
                if term:
                    sep = "&" if "?" in self.search_url_prefix else "?"
                    url = f"{self.search_url_prefix}{urllib.parse.quote_plus(term)}{sep}search_type=1"
                    parts[0] = f'<a href="{url}" class="symbol-link">{parts[0]}'
                    parts[-1] = parts[-1] + "</a>"

            if len(parts) > 1:
                for part in parts[:-1]:
                    if line:
                        if lspan != cspan and part:
                            line.extend(((lspan and "</span>"), cspan, part, (cspan and "</span>"), lsep))
                        else:
                            line.extend((part, (lspan and "</span>"), lsep))
                        yield 1, "".join(line)
                        line = []
                    elif part:
                        yield 1, "".join((cspan, part, (cspan and "</span>"), lsep))
                    else:
                        yield 1, lsep
            last = parts[-1]
            if line and last:
                if lspan != cspan:
                    line.extend(((lspan and "</span>"), cspan, last))
                    lspan = cspan
                else:
                    line.append(last)
            elif last:
                line = [cspan, last]
                lspan = cspan

        if line:
            line.extend(((lspan and "</span>"), lsep))
            yield 1, "".join(line)


def get_lexer_for_code(filename: str, content: str, lang: str = ""):
    """
    Selects the most suitable Pygments lexer based on explicit language name,
    filename, or content, falling back to TextLexer.
    """
    if lang and lang != "plaintext":
        try:
            return get_lexer_by_name(lang, stripnl=False)
        except ClassNotFound:
            pass

    try:
        return get_lexer_for_filename(filename, content, stripnl=False)
    except ClassNotFound:
        return TextLexer(stripnl=False)


def highlight_code(
    content: str,
    filename: str,
    lang: str = "",
    style: str = "github-dark",
    search_url_prefix: str = "/search_results?search_term=",
) -> Tuple[str, str]:
    """
    Highlights code using Pygments and SymbolSearchHtmlFormatter.
    Returns (highlighted_html, pygments_css).
    """
    lexer = get_lexer_for_code(filename, content, lang)
    formatter = SymbolSearchHtmlFormatter(
        search_url_prefix=search_url_prefix,
        linenos="table",
        linespans="line",
        anchorlinenos=True,
        style=style,
    )
    highlighted_html = highlight(content, lexer, formatter)
    pygments_css = f"/* Pygments style: {style} */\n" + formatter.get_style_defs(".highlight")
    return highlighted_html, pygments_css
