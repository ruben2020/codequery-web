#
# codequery-web
# Copyright (C) 2026 ruben2020 https://github.com/ruben2020/
# SPDX-License-Identifier: MIT
#

import unittest
from src.app import app
from src.search_processor import SearchProcessor, resolve_relative_path


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


if __name__ == "__main__":
    unittest.main()
