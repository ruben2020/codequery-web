#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
# SPDX-License-Identifier: MIT
#

import json
from pathlib import Path
from urllib.parse import unquote
from flask import Flask, abort, make_response, render_template, request, url_for
from .directory_processor import DirectoryProcessor, get_folder_breadcrumbs
from .file_processor import FileProcessor
from .search_processor import SearchProcessor
from .validator import get_base_dir

# Resolve the project root folder explicitly
ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT_DIR / "templates"

app = Flask(__name__, template_folder=str(TEMPLATES_DIR))

MAX_HISTORY_ITEMS = 5
SEARCH_TERM_COOKIE = "search_term_history"
PATH_FILTER_COOKIE = "path_filter_history"
COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def get_history_from_cookie(cookie_name: str) -> list[str]:
    raw = request.cookies.get(cookie_name, "")
    if not raw:
        return []
    for candidate in (raw, unquote(raw)):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                result: list[str] = []
                for item in parsed:
                    if isinstance(item, str):
                        val = item.strip()
                        if val and val not in result:
                            result.append(val)
                return result[:MAX_HISTORY_ITEMS]
        except (ValueError, TypeError):
            continue
    return []


def update_history(history: list[str], new_entry: str) -> list[str]:
    cleaned = new_entry.strip()
    if not cleaned:
        return history[:MAX_HISTORY_ITEMS]
    updated = [cleaned] + [item for item in history if item != cleaned]
    return updated[:MAX_HISTORY_ITEMS]


@app.route("/")
def index():
    return browse_directory()


@app.route("/opendir")
def browse_directory():
    path_param = request.args.get("p", "")
    processor = DirectoryProcessor(path_param)

    return render_template(
        "browser.html",
        items=processor.get_contents(),
        current_path=path_param,
        parent_path=processor.get_parent_path(),
        folder_levels=get_folder_breadcrumbs(path_param),
    )


@app.route("/openfile")
def view_file():
    path_param = request.args.get("p", "")
    if not path_param:
        abort(400, "Missing path parameter 'p'")

    processor = FileProcessor(path_param)
    data = processor.get_file_data()

    clean_p = path_param.replace("\\", "/").strip("/")
    parent_dir = "/".join(clean_p.split("/")[:-1]) if "/" in clean_p else ""

    return render_template(
        "viewer.html",
        content=data["highlighted_content"],
        raw_content=data["content"],
        highlighted_content=data["highlighted_content"],
        pygments_css=data["pygments_css"],
        filename=data["filename"],
        lang=data["lang"],
        current_file=data["filename"],
        folder_levels=get_folder_breadcrumbs(parent_dir),
    )


@app.route("/search_form")
@app.route("/search_query")
def search_query():
    search_term_history = get_history_from_cookie(SEARCH_TERM_COOKIE)
    path_filter_history = get_history_from_cookie(PATH_FILTER_COOKIE)
    return render_template(
        "search_query.html",
        search_term="",
        path_filter="",
        search_type="1",
        exact_match=False,
        search_term_history=search_term_history,
        path_filter_history=path_filter_history,
    )


@app.route("/search/<path:term>", methods=["GET", "POST"])
@app.route("/search", methods=["GET", "POST"])
@app.route("/search_results", methods=["GET", "POST"])
def search_results(term: str = ""):
    if request.method == "POST":
        search_term = request.form.get("search_term", "").strip()
        path_filter = request.form.get("path_filter", "").strip()
        search_type = request.form.get("search_type", "1").strip()
        exact_match = bool(request.form.get("exact_match"))
    else:
        # GET request
        search_term = (
            term
            or request.args.get("search_term")
            or request.args.get("term")
            or request.args.get("q")
            or ""
        ).strip()
        path_filter = (
            request.args.get("path_filter")
            or request.args.get("filter")
            or ""
        ).strip()
        search_type = (
            request.args.get("search_type")
            or request.args.get("type")
            or "1"
        ).strip()
        exact_val = request.args.get("exact_match") or request.args.get("exact") or ""
        exact_match = bool(exact_val and exact_val.lower() not in ("0", "false", "no"))

    if not search_type:
        search_type = "1"

    search_term_history = get_history_from_cookie(SEARCH_TERM_COOKIE)
    path_filter_history = get_history_from_cookie(PATH_FILTER_COOKIE)

    if search_term:
        search_term_history = update_history(search_term_history, search_term)
    if path_filter:
        path_filter_history = update_history(path_filter_history, path_filter)

    searched = bool(search_term)
    results = []
    if searched:
        processor = SearchProcessor(
            search_term=search_term,
            search_type=search_type,
            path_filter=path_filter,
            exact_match=exact_match,
        )
        results = processor.execute()

    response = make_response(
        render_template(
            "search_results.html",
            search_term=search_term,
            path_filter=path_filter,
            search_type=search_type,
            exact_match=exact_match,
            results=results,
            searched=searched,
            search_term_history=search_term_history,
            path_filter_history=path_filter_history,
        )
    )
    if search_term:
        response.set_cookie(
            SEARCH_TERM_COOKIE,
            json.dumps(search_term_history),
            max_age=COOKIE_MAX_AGE,
            samesite="Lax",
        )
    if path_filter:
        response.set_cookie(
            PATH_FILTER_COOKIE,
            json.dumps(path_filter_history),
            max_age=COOKIE_MAX_AGE,
            samesite="Lax",
        )
    return response
