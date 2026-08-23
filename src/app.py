#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

from pathlib import Path
from flask import Flask, abort, render_template, request
from .directory_processor import DirectoryProcessor
from .file_processor import FileProcessor
from .validator import BASE_DIR

# Resolve the project root folder explicitly
ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT_DIR / "templates"

app = Flask(__name__, template_folder=str(TEMPLATES_DIR))


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
    )


@app.route("/openfile")
def view_file():
    path_param = request.args.get("p", "")
    if not path_param:
        abort(400, "Missing path parameter 'p'")

    processor = FileProcessor(path_param)
    data = processor.get_file_data()

    return render_template(
        "viewer.html",
        content=data["content"],
        filename=data["filename"],
        lang=data["lang"],
    )
