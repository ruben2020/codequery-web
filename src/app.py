#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

from flask import Flask, render_template

app = Flask(__name__, template_folder='../templates')

@app.route('/')
def home():
    # Context dictionary to pass dynamic data to the HTML template
    context = {
        "title": "Open Source Backend",
        "status": "Online",
        "framework": "Flask + Gunicorn + Caddy"
    }
    return render_template('index.html', **context)

if __name__ == '__main__':
    # Used only for local development debugging
    app.run(host='127.0.0.1', port=5000, debug=True)
