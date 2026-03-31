"""Tests for src/slicer.py — Backward slicing algorithm."""

import os
import pytest
from src.callgraph import build_callgraph
from src.slicer import backward_slice, Slice

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestBackwardSlice:
    @pytest.fixture
    def demo_graph(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        return build_callgraph(repo)

    @pytest.fixture
    def multi_graph(self):
        repo = os.path.join(FIXTURES, "multi_file_repo")
        return build_callgraph(repo)

    def test_basic_slice(self, demo_graph):
        s = backward_slice(demo_graph, "scraper.scrape")
        assert s.target == "scraper.scrape"
        assert len(s.dependencies) > 0
        assert s.total_lines > 0
        assert s.original_lines > 0

    def test_slice_includes_dependencies(self, demo_graph):
        s = backward_slice(demo_graph, "scraper.scrape")
        dep_names = [d.split(".")[-1] for d in s.dependencies]
        assert "scrape" in dep_names
        assert "log" in dep_names or "get_config" in dep_names

    def test_slice_reduction_ratio(self, demo_graph):
        s = backward_slice(demo_graph, "scraper.scrape")
        assert 0 <= s.reduction_ratio <= 1

    def test_slice_code_not_empty(self, demo_graph):
        s = backward_slice(demo_graph, "scraper.scrape")
        assert len(s.code) > 0
        assert "def" in s.code

    def test_leaf_function_slice(self, demo_graph):
        s = backward_slice(demo_graph, "utils.log")
        assert s.target == "utils.log"
        assert len(s.dependencies) == 1
        assert s.dependencies[0] == "utils.log"

    def test_nonexistent_target(self, demo_graph):
        s = backward_slice(demo_graph, "nonexistent.func")
        assert s.target == "nonexistent.func"
        assert len(s.dependencies) == 0

    def test_max_depth_limits(self, demo_graph):
        s_full = backward_slice(demo_graph, "scraper.scrape")
        s_limited = backward_slice(demo_graph, "scraper.scrape", max_depth=1)
        assert len(s_limited.dependencies) <= len(s_full.dependencies)

    def test_no_infinite_loop_on_cycles(self, demo_graph):
        """Backward slicer must handle cycles without infinite loops."""
        s = backward_slice(demo_graph, "scraper.scrape")
        assert s is not None

    def test_cross_file_slice(self, multi_graph):
        s = backward_slice(multi_graph, "main.main")
        assert len(s.dependencies) > 1
        dep_files = set()
        for d in s.dependencies:
            if d in multi_graph.functions:
                dep_files.add(multi_graph.functions[d].filepath)
        assert len(dep_files) > 1

    def test_to_dict(self, demo_graph):
        s = backward_slice(demo_graph, "scraper.scrape")
        d = s.to_dict()
        assert "target" in d
        assert "dependencies" in d
        assert "code" in d
        assert "reduction_ratio" in d
        assert isinstance(d["reduction_ratio"], float)

    def test_partial_name_resolution(self, demo_graph):
        """Should resolve short names like 'scraper.scrape'."""
        s = backward_slice(demo_graph, "scraper.scrape")
        assert s.target == "scraper.scrape"
        assert len(s.dependencies) > 0
