#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
# SPDX-License-Identifier: MIT
#

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, unquote
from flask import Flask, Response, abort, make_response, redirect, render_template, request, url_for
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
THEME_COOKIE = "theme"
DEFAULT_THEME = "dark"
COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def get_current_theme() -> str:
    if request.view_args and "theme_name" in request.view_args:
        view_theme = str(request.view_args.get("theme_name", "")).strip().lower()
        if view_theme in ("light", "dark"):
            return view_theme
    theme_arg = request.args.get("theme", "").strip().lower()
    if theme_arg in ("light", "dark"):
        return theme_arg
    cookie_val = request.cookies.get(THEME_COOKIE, "").strip().lower()
    if cookie_val in ("light", "dark"):
        return cookie_val
    return DEFAULT_THEME


def get_theme_toggle_url(current_theme: str) -> str:
    target_theme = "light" if current_theme == "dark" else "dark"
    args = request.args.to_dict(flat=True)
    if request.method == "POST":
        for field in ("search_term", "path_filter", "search_type"):
            val = request.form.get(field, "").strip()
            if val:
                args[field] = val
        if request.form.get("exact_match"):
            args["exact_match"] = "1"
    args["theme"] = target_theme
    return f"{request.path}?{urlencode(args)}"


def get_db_last_indexed() -> str:
    db_path = get_base_dir() / ".vscode" / "codequery" / "cq.db"
    try:
        if db_path.exists():
            mtime = db_path.stat().st_mtime
            return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    return "N/A"


@app.context_processor
def inject_theme_context():
    theme = get_current_theme()
    pygments_style = "github-light" if theme == "light" else "github-dark"
    theme_toggle_label = (
        "Switch to Dark Theme" if theme == "light" else "Switch to Light Theme"
    )
    return {
        "theme": theme,
        "pygments_style": pygments_style,
        "theme_toggle_label": theme_toggle_label,
        "theme_toggle_url": get_theme_toggle_url(theme),
        "last_indexed": get_db_last_indexed(),
    }


@app.after_request
def persist_theme_cookie(response):
    theme = get_current_theme()
    response.set_cookie(
        THEME_COOKIE,
        theme,
        max_age=COOKIE_MAX_AGE,
        samesite="Lax",
    )
    return response


@app.route("/set_theme/<theme_name>")
@app.route("/set_theme")
def set_theme(theme_name: str = ""):
    chosen = (theme_name or request.args.get("theme", "")).strip().lower()
    if chosen not in ("light", "dark"):
        chosen = DEFAULT_THEME
    next_url = request.args.get("next") or request.referrer or url_for("index")
    response = make_response(redirect(next_url))
    response.set_cookie(
        THEME_COOKIE,
        chosen,
        max_age=COOKIE_MAX_AGE,
        samesite="Lax",
    )
    return response


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

    if request.args.get("raw", "").strip().lower() in ("1", "true", "yes"):
        return raw_file(path_param)

    theme = get_current_theme()
    processor = FileProcessor(path_param, theme=theme)
    data = processor.get_file_data(theme=theme)

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
        current_path=clean_p,
        folder_levels=get_folder_breadcrumbs(parent_dir),
    )


@app.route("/rawfile/<path:file_path>")
@app.route("/raw_file/<path:file_path>")
@app.route("/raw/<path:file_path>")
@app.route("/rawfile")
@app.route("/raw_file")
@app.route("/raw")
def raw_file(file_path: str = ""):
    path_param = (
        file_path
        or request.args.get("p")
        or request.args.get("path")
        or request.args.get("file")
        or ""
    ).strip()
    if not path_param:
        abort(400, "Missing path parameter 'p'")

    processor = FileProcessor(path_param)
    raw_text = processor.get_raw_content()
    return Response(raw_text, mimetype="text/plain; charset=utf-8")


@app.route("/git_history/<path:file_path>")
@app.route("/githistory/<path:file_path>")
@app.route("/gitlog/<path:file_path>")
@app.route("/file_git_history/<path:file_path>")
@app.route("/git_history")
@app.route("/githistory")
@app.route("/gitlog")
@app.route("/file_git_history")
def file_git_history(file_path: str = ""):
    path_param = (
        file_path
        or request.args.get("p")
        or request.args.get("path")
        or request.args.get("file")
        or ""
    ).strip()
    if not path_param:
        abort(400, "Missing path parameter 'p'")

    theme = get_current_theme()
    processor = FileProcessor(path_param, theme=theme)
    git_log = processor.get_git_history()

    clean_p = path_param.replace("\\", "/").strip("/")
    parent_dir = "/".join(clean_p.split("/")[:-1]) if "/" in clean_p else ""

    return render_template(
        "file_git_history.html",
        git_log=git_log,
        content=git_log,
        filename=processor.abs_path.name,
        current_file=processor.abs_path.name,
        current_path=clean_p,
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
