#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
# SPDX-License-Identifier: MIT
#

# wsgi.py
from src.app import app
from src.validator import BASE_DIR

# Ensures the 'share' directory exists before running
BASE_DIR.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    app.run(debug=True)
