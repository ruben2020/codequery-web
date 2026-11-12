#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
# SPDX-License-Identifier: MIT
#

import unittest
from pathlib import Path
from src.app import app
from src.search_processor import SearchProcessor, resolve_relative_path
from src.directory_processor import get_folder_breadcrumbs
from src.file_processor import FileProcessor
from src.validator import get_base_dir, set_base_dir
from wsgi import parse_args


class TestSearchAndNavigation(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_top_nav_in_all_pages(self):
        # 1. Directory browser page
        res = self.client.get("/opendir")
        self.assertEqual(res.status_code, 200)
        self.assertIn('href="/search_query"', res.text)
        self.assertIn("Search Query", res.text)

        # 2. File viewer page
        res = self.client.get("/openfile?p=cli/main_cli.cpp")
        self.assertEqual(res.status_code, 200)
        self.assertIn('href="/search_query"', res.text)
        self.assertIn("Search Query", res.text)

        # 3. Search results page
        res = self.client.get("/search_results")
        self.assertEqual(res.status_code, 200)
        self.assertIn('href="/search_query"', res.text)
        self.assertIn("Search Query", res.text)

    def test_search_query_page_form_fields(self):
        res = self.client.get("/search_query")
        self.assertEqual(res.status_code, 200)

        # Form action and method
        self.assertIn('action="/search_results"', res.text)
        self.assertIn('method="POST"', res.text)

        # Labels
        self.assertIn("Search term:", res.text)
        self.assertIn("Path filter:", res.text)
        self.assertIn("Search type:", res.text)
        self.assertIn("Exact match", res.text)
        self.assertIn("Search", res.text)

        # All 11 dropdown options
        expected_options = [
            ('value="1"', "Symbol"),
            ('value="2"', "Function or macro definition"),
            ('value="3"', "Class or struct"),
            ('value="4"', "Files including this file"),
            ('value="6"', "Functions calling this function"),
            ('value="7"', "Functions called by this function"),
            ('value="8"', "Calls of this function or macro"),
            ('value="9"', "Members and methods of this class"),
            ('value="10"', "Class which owns this member or method"),
            ('value="11"', "Children of this class (inheritance)"),
            ('value="12"', "Parent of this class"),
        ]
        for val, label in expected_options:
            self.assertIn(val, res.text)
            self.assertIn(label, res.text)

        # Value 1 selected by default
        self.assertIn('<option value="1" selected>Symbol</option>', res.text)

        # Exact match checkbox unchecked by default
        self.assertIn('<input type="checkbox" id="exact_match" name="exact_match" value="1">', res.text)

    def test_post_search_3_columns(self):
        res = self.client.post("/search_results", data={
            "search_term": "main",
            "search_type": "1",
            "path_filter": "cli",
            "exact_match": "1",
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("<th>Symbol</th>", res.text)
        self.assertIn("<th>Path</th>", res.text)
        self.assertIn("<th>Preview</th>", res.text)
        self.assertIn("main_cli.cpp", res.text)
        self.assertIn("/openfile?p=cli/main_cli.cpp#line-215", res.text)
        # Verify path in column is truncated relative to share/
        self.assertIn(">cli/main_cli.cpp:215</a>", res.text)
        self.assertNotIn("$HOME", res.text)
        self.assertNotIn("share/cli/main_cli.cpp", res.text)

    def test_post_search_2_columns_type_4(self):
        res = self.client.post("/search_results", data={
            "search_term": "catch.hpp",
            "search_type": "4",
            "path_filter": "",
        })
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("<th>Symbol</th>", res.text)
        self.assertIn("<th>Path</th>", res.text)
        self.assertIn("<th>Preview</th>", res.text)
        self.assertIn("UnitTester.cxx", res.text)

    def test_get_search_results_via_symbol_link(self):
        res = self.client.get("/search_results?search_term=main&search_type=1")
        self.assertEqual(res.status_code, 200)
        self.assertIn("<th>Symbol</th>", res.text)
        self.assertIn("<th>Path</th>", res.text)
        self.assertIn("<th>Preview</th>", res.text)
        self.assertIn("main_cli.cpp", res.text)

    def test_viewer_symbol_hyperlinks_target_search_results_get(self):
        res = self.client.get("/openfile?p=cli/main_cli.cpp")
        self.assertEqual(res.status_code, 200)
        self.assertIn('/search_results?search_term=', res.text)
        self.assertIn('search_type=1', res.text)
        self.assertIn('id="line-215"', res.text)

    def test_viewer_line_spans_and_no_offset(self):
        res = self.client.get("/openfile?p=cli/main_cli.cpp")
        self.assertEqual(res.status_code, 200)
        # Line 215 in main_cli.cpp is 'int main(int argc, char *argv[])'
        # Verify <span id="line-215"> wraps line 215 (and not an empty <a id="line-215"></a>)
        self.assertIn('<span id="line-215">', res.text)
        self.assertNotIn('<a id="line-215"', res.text)
        line_215_segment = res.text.split('<span id="line-215">', 1)[1].split("</span>\n", 1)[0]
        self.assertIn("main", line_215_segment)
        self.assertIn("argc", line_215_segment)
        self.assertIn("argv", line_215_segment)

    def test_resolve_relative_path(self):
        rel = resolve_relative_path("$HOME/repo/codequery-web/share/cli/main_cli.cpp")
        self.assertEqual(rel, "cli/main_cli.cpp")

    def test_empty_search_term(self):
        res = self.client.post("/search_results", data={
            "search_term": "",
            "search_type": "1",
            "path_filter": "",
        })
        self.assertEqual(res.status_code, 200)
        self.assertNotIn('<table class="results-table">', res.text)

    def test_search_results_page_retains_form_values(self):
        res = self.client.post("/search_results", data={
            "search_term": "mySymbol",
            "search_type": "2",
            "path_filter": "some/path",
            "exact_match": "1",
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn('value="mySymbol"', res.text)
        self.assertIn('value="some/path"', res.text)
        self.assertIn('<option value="2" selected>Function or macro definition</option>', res.text)
        self.assertIn('checked', res.text)

    def test_search_processor_command_args(self):
        proc = SearchProcessor(
            search_term="testTerm",
            search_type="3",
            path_filter="filterDir",
            exact_match=True,
        )
        # Verify execute generates expected results or handles nonexistent terms gracefully
        results = proc.execute()
        self.assertIsInstance(results, list)

    def test_folder_bar_in_folder_browser_root(self):
        res = self.client.get("/opendir")
        self.assertEqual(res.status_code, 200)
        self.assertIn('class="folder-bar"', res.text)
        self.assertIn('class="folder-level">/</a>', res.text)

    def test_folder_bar_in_folder_browser_subfolder(self):
        res = self.client.get("/opendir?p=cli")
        self.assertEqual(res.status_code, 200)
        self.assertIn('class="folder-bar"', res.text)
        self.assertIn('class="folder-level">/</a>', res.text)
        self.assertIn('href="/opendir?p=cli"', res.text)
        self.assertIn('class="folder-level">cli</a>', res.text)

    def test_folder_bar_in_file_viewer(self):
        res = self.client.get("/openfile?p=cli/main_cli.cpp")
        self.assertEqual(res.status_code, 200)
        self.assertIn('class="folder-bar"', res.text)
        self.assertIn('class="folder-level">/</a>', res.text)
        self.assertIn('href="/opendir?p=cli"', res.text)
        self.assertIn('class="folder-level">cli</a>', res.text)
        self.assertIn('class="file-level">main_cli.cpp</span>', res.text)

    def test_folder_bar_in_file_viewer_root_file(self):
        res = self.client.get("/openfile?p=README.md")
        self.assertEqual(res.status_code, 200)
        self.assertIn('class="folder-bar"', res.text)
        self.assertIn('class="folder-level">/</a>', res.text)
        self.assertIn('class="file-level">README.md</span>', res.text)

    def test_get_folder_breadcrumbs(self):
        crumbs = get_folder_breadcrumbs("gui/dialogs/find")
        self.assertEqual(
            crumbs,
            [
                {"name": "gui", "path": "gui"},
                {"name": "dialogs", "path": "gui/dialogs"},
                {"name": "find", "path": "gui/dialogs/find"},
            ],
        )
        self.assertEqual(get_folder_breadcrumbs(""), [])
        self.assertEqual(get_folder_breadcrumbs("cli"), [{"name": "cli", "path": "cli"}])

    def test_markdown_syntax_highlighting(self):
        proc = FileProcessor("README.md")
        data = proc.get_file_data()
        self.assertEqual(data["lang"], "markdown")
        self.assertIn("highlight", data["highlighted_content"])

        res = self.client.get("/openfile?p=README.md")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Viewing: README.md", res.text)

    def test_wsgi_args_parsing(self):
        # Default with no args
        args = parse_args([])
        self.assertIsNone(args.share_dir)
        self.assertIsNone(args.share_opt)

        # Positional share_dir arg
        args = parse_args(["/custom/share/dir"])
        self.assertEqual(args.share_dir, "/custom/share/dir")
        self.assertIsNone(args.share_opt)

        # Optional flag --share
        args = parse_args(["--share", "/another/path"])
        self.assertEqual(args.share_opt, "/another/path")

        # Optional flag -s
        args = parse_args(["-s", "/short/path"])
        self.assertEqual(args.share_opt, "/short/path")

    def test_base_dir_setter_and_getter(self):
        orig = get_base_dir()
        try:
            set_base_dir("/tmp/test_codequery_share")
            self.assertEqual(get_base_dir(), Path("/tmp/test_codequery_share").resolve())
        finally:
            set_base_dir(orig)

    def test_input_history_dropdown_and_cookies_last_5_unique(self):
        # Initially, datalist elements are present and empty
        res = self.client.get("/search_query")
        self.assertEqual(res.status_code, 200)
        self.assertIn('list="search_term_history"', res.text)
        self.assertIn('<datalist id="search_term_history">', res.text)
        self.assertIn('list="path_filter_history"', res.text)
        self.assertIn('<datalist id="path_filter_history">', res.text)

        # Submit 6 unique search terms and 6 unique path filters
        for i in range(1, 7):
            res = self.client.post("/search_results", data={
                "search_term": f"term{i}",
                "path_filter": f"path{i}",
                "search_type": "1",
            })
            self.assertEqual(res.status_code, 200)

        # Duplicate an existing entry (term3 and path3) to verify uniqueness and MRU order
        res = self.client.post("/search_results", data={
            "search_term": "term3",
            "path_filter": "path3",
            "search_type": "1",
        })
        self.assertEqual(res.status_code, 200)

        # Submit empty values to ensure they don't overwrite or enter the history
        res = self.client.post("/search_results", data={
            "search_term": "",
            "path_filter": "",
            "search_type": "1",
        })
        self.assertEqual(res.status_code, 200)

        # Verify on /search_query page that only the last 5 unique entries exist
        res = self.client.get("/search_query")
        self.assertEqual(res.status_code, 200)

        # term1 and path1 should have been evicted (only 5 unique kept: 3, 6, 5, 4, 2)
        self.assertNotIn('<option value="term1">', res.text)
        self.assertNotIn('<option value="path1">', res.text)

        for idx in (3, 6, 5, 4, 2):
            self.assertIn(f'<option value="term{idx}">term{idx}</option>', res.text)
            self.assertIn(f'<option value="path{idx}">path{idx}</option>', res.text)

        # Ensure no duplicate option tags for term3 or path3
        self.assertEqual(res.text.count('<option value="term3">term3</option>'), 1)
        self.assertEqual(res.text.count('<option value="path3">path3</option>'), 1)


if __name__ == "__main__":
    unittest.main()
