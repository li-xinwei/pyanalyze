"""Tests for src/export.py — JSON and DOT export."""

import json
import os
import tempfile
import pytest
from src.callgraph import build_callgraph
from src.export import to_json, to_dot, export_json, export_dot

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestToJson:
    def test_json_structure(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)
        result = to_json(graph)

        assert "nodes" in result
        assert "edges" in result
        assert "metrics" in result
        assert "files" in result

    def test_node_fields(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)
        result = to_json(graph)

        node = result["nodes"][0]
        assert "id" in node
        assert "name" in node
        assert "file" in node
        assert "lineno" in node
        assert "lines" in node
        assert "complexity" in node
        assert "fan_in" in node
        assert "fan_out" in node
        assert "source_code" in node

    def test_edge_fields(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)
        result = to_json(graph)

        if result["edges"]:
            edge = result["edges"][0]
            assert "source" in edge
            assert "target" in edge

    def test_metrics_fields(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)
        result = to_json(graph)

        m = result["metrics"]
        assert "total_files" in m
        assert "total_functions" in m
        assert "total_edges" in m
        assert "avg_complexity" in m

    def test_json_serializable(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)
        result = to_json(graph)
        serialized = json.dumps(result)
        assert len(serialized) > 0


class TestToDot:
    def test_dot_output(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)
        dot = to_dot(graph)

        assert dot.startswith("digraph callgraph {")
        assert dot.strip().endswith("}")
        assert "->" in dot

    def test_dot_has_nodes(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)
        dot = to_dot(graph)
        assert "label=" in dot


class TestExportFiles:
    def test_export_json_file(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmppath = f.name

        try:
            export_json(graph, tmppath)
            with open(tmppath) as f:
                data = json.load(f)
            assert "nodes" in data
            assert len(data["nodes"]) == 15
        finally:
            os.unlink(tmppath)

    def test_export_dot_file(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        graph = build_callgraph(repo)

        with tempfile.NamedTemporaryFile(suffix=".dot", delete=False) as f:
            tmppath = f.name

        try:
            export_dot(graph, tmppath)
            with open(tmppath) as f:
                content = f.read()
            assert "digraph" in content
        finally:
            os.unlink(tmppath)
