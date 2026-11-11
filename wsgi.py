#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
# SPDX-License-Identifier: MIT
#

import argparse
import sys
from src.app import app
from src.validator import get_base_dir, set_base_dir


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="codequery-web - Web interface for CodeQuery"
    )
    parser.add_argument(
        "share_dir",
        nargs="?",
        default=None,
        help="Optional path to the share/ folder containing search target and cq.db (default: ./share)",
    )
    parser.add_argument(
        "-s",
        "--share",
        dest="share_opt",
        default=None,
        help="Optional path to the share/ folder",
    )
    return parser.parse_args(argv)


# Ensures the base directory exists before running
get_base_dir().mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    share_path = args.share_opt or args.share_dir
    if share_path:
        set_base_dir(share_path)

    base_dir = get_base_dir()
    base_dir.mkdir(parents=True, exist_ok=True)

    app.run(debug=True)
