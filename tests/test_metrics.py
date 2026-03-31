"""Tests for src/metrics.py — Cyclomatic complexity and metrics."""

import os
import pytest
from src.metrics import (
    cyclomatic_complexity,
    compute_complexity_from_source,
    function_metrics,
    repo_metrics,
)
from src.callgraph import build_callgraph
import ast

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestCyclomaticComplexity:
    def _get_func_node(self, source):
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node
        return None

    def test_simple_function(self):
        source = "def foo():\n    return 1\n"
        node = self._get_func_node(source)
        assert cyclomatic_complexity(node) == 1

    def test_single_if(self):
        source = "def foo(x):\n    if x:\n        return 1\n    return 0\n"
        node = self._get_func_node(source)
        assert cyclomatic_complexity(node) == 2

    def test_if_elif_else(self):
        source = (
            "def foo(x):\n"
            "    if x > 0:\n"
            "        return 1\n"
            "    elif x < 0:\n"
            "        return -1\n"
            "    else:\n"
            "        return 0\n"
        )
        node = self._get_func_node(source)
        assert cyclomatic_complexity(node) == 3

    def test_for_loop(self):
        source = "def foo(items):\n    for i in items:\n        pass\n"
        node = self._get_func_node(source)
        assert cyclomatic_complexity(node) == 2

    def test_while_loop(self):
        source = "def foo():\n    while True:\n        break\n"
        node = self._get_func_node(source)
        assert cyclomatic_complexity(node) == 2

    def test_try_except(self):
        source = (
            "def foo():\n"
            "    try:\n"
            "        pass\n"
            "    except ValueError:\n"
            "        pass\n"
        )
        node = self._get_func_node(source)
        assert cyclomatic_complexity(node) == 2

    def test_boolean_operators(self):
        source = "def foo(a, b, c):\n    if a and b or c:\n        pass\n"
        node = self._get_func_node(source)
        cc = cyclomatic_complexity(node)
        assert cc >= 3

    def test_ternary(self):
        source = "def foo(x):\n    return 1 if x else 0\n"
        node = self._get_func_node(source)
        assert cyclomatic_complexity(node) == 2


class TestComputeComplexityFromSource:
    def test_simple(self):
        source = "def foo():\n    return 1\n"
        assert compute_complexity_from_source(source) == 1

    def test_complex(self):
        source = (
            "def foo(x):\n"
            "    if x > 0:\n"
            "        for i in range(x):\n"
            "            if i % 2 == 0:\n"
            "                pass\n"
        )
        assert compute_complexity_from_source(source) == 4

    def test_syntax_error(self):
        assert compute_complexity_from_source("not valid python {{{") == 1


class TestFunctionMetrics:
    def test_demo_repo(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)
        metrics = function_metrics(graph)

        assert len(metrics) == len(graph.functions)
        for qname, m in metrics.items():
            assert "complexity" in m
            assert "fan_in" in m
            assert "fan_out" in m
            assert "lines" in m
            assert m["complexity"] >= 1


class TestRepoMetrics:
    def test_demo_repo(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)
        m = repo_metrics(graph)

        assert m["total_files"] == 5
        assert m["total_functions"] == 15
        assert m["total_edges"] > 0
        assert m["avg_complexity"] >= 1
        assert 0 <= m["avg_slice_reduction"] <= 1

    def test_multi_file_repo(self):
        repo = os.path.join(FIXTURES, "multi_file_repo")
        graph = build_callgraph(repo)
        m = repo_metrics(graph)

        assert m["total_files"] == 4
        assert m["total_functions"] > 0
