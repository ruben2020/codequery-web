#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

# wsgi.py
from src.app import app
from src.validator import BASE_DIR

# Ensures the 'share' directory exists before running
BASE_DIR.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    app.run(debug=True)
