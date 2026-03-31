"""Tests for src/callgraph.py — Call graph construction."""

import os
import pytest
from src.callgraph import build_callgraph, CallGraph

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestBuildCallgraph:
    def test_multi_file_repo(self):
        repo = os.path.join(FIXTURES, "multi_file_repo")
        graph = build_callgraph(repo)

        assert len(graph.functions) > 0
        assert len(graph.files) == 4
        assert "main.main" in graph.functions

    def test_cross_file_edges(self):
        repo = os.path.join(FIXTURES, "multi_file_repo")
        graph = build_callgraph(repo)

        callees = graph.get_callees("main.main")
        callee_names = [c.split(".")[-1] for c in callees]
        assert "validate" in callee_names
        assert "square" in callee_names

    def test_demo_repo(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)

        assert len(graph.functions) == 15
        assert len(graph.files) == 5
        assert len(graph.edges) > 0

    def test_scraper_calls(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)

        callees = graph.get_callees("scraper.scrape")
        callee_names = [c.split(".")[-1] for c in callees]
        assert "get_config" in callee_names
        assert "fetch_page" in callee_names
        assert "save_result" in callee_names
        assert "log" in callee_names

    def test_external_calls_tracked(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)
        assert len(graph.external_calls) > 0

    def test_no_crash_on_unresolved(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)
        assert graph is not None

    def test_get_callers(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)

        callers = graph.get_callers("utils.log")
        assert len(callers) > 0

    def test_to_networkx(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)
        G = graph.to_networkx()

        assert G.number_of_nodes() == len(graph.functions)
        assert G.number_of_edges() == len(graph.edges)

    def test_to_dict(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)
        d = graph.to_dict()

        assert "functions" in d
        assert "edges" in d
        assert "files" in d
        assert "external_calls" in d
