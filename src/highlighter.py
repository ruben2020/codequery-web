#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
# SPDX-License-Identifier: MIT
#

import urllib.parse
from typing import Tuple
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import (
    TextLexer,
    get_lexer_by_name,
    get_lexer_for_filename,
)
from pygments.token import Token
from pygments.util import ClassNotFound


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
            return get_lexer_by_name(lang)
        except ClassNotFound:
            pass

    try:
        return get_lexer_for_filename(filename, content)
    except ClassNotFound:
        return TextLexer()


def highlight_code(
    content: str,
    filename: str,
    lang: str = "",
    style: str = "rrt",
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
        lineanchors="line",
        anchorlinenos=True,
        style=style,
    )
    highlighted_html = highlight(content, lexer, formatter)
    pygments_css = formatter.get_style_defs(".highlight")
    return highlighted_html, pygments_css
