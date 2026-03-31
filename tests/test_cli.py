"""Tests for src/cli.py — CLI interface."""

import json
import os
import tempfile
import pytest
from click.testing import CliRunner
from src.cli import cli

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestAnalyzeCommand:
    def test_analyze_demo_repo(self):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "analyze", os.path.join(FIXTURES, "demo_repo")
        ])
        assert result.exit_code == 0
        assert "Functions: 15" in result.output
        assert "Files: 5" in result.output

    def test_analyze_with_output(self):
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmppath = f.name

        try:
            result = runner.invoke(cli, [
                "analyze", os.path.join(FIXTURES, "demo_repo"),
                "--output", tmppath
            ])
            assert result.exit_code == 0
            assert "Output written to" in result.output

            with open(tmppath) as f:
                data = json.load(f)
            assert len(data["nodes"]) == 15
        finally:
            os.unlink(tmppath)

    def test_analyze_dot_format(self):
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(suffix=".dot", delete=False) as f:
            tmppath = f.name

        try:
            result = runner.invoke(cli, [
                "analyze", os.path.join(FIXTURES, "demo_repo"),
                "--output", tmppath, "--format", "dot"
            ])
            assert result.exit_code == 0
            with open(tmppath) as f:
                content = f.read()
            assert "digraph" in content
        finally:
            os.unlink(tmppath)


class TestSliceCommand:
    def test_slice_command(self):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "slice", os.path.join(FIXTURES, "demo_repo"),
            "--target", "scraper.scrape"
        ])
        assert result.exit_code == 0
        assert "Dependencies:" in result.output

    def test_slice_with_output(self):
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmppath = f.name

        try:
            result = runner.invoke(cli, [
                "slice", os.path.join(FIXTURES, "demo_repo"),
                "--target", "scraper.scrape",
                "--output", tmppath
            ])
            assert result.exit_code == 0
            with open(tmppath) as f:
                data = json.load(f)
            assert data["target"] == "scraper.scrape"
            assert len(data["dependencies"]) > 0
        finally:
            os.unlink(tmppath)

    def test_slice_with_max_depth(self):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "slice", os.path.join(FIXTURES, "demo_repo"),
            "--target", "scraper.scrape",
            "--max-depth", "1"
        ])
        assert result.exit_code == 0


class TestReportCommand:
    def test_report_command(self):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "report", os.path.join(FIXTURES, "demo_repo")
        ])
        assert result.exit_code == 0
        assert "Repository Report" in result.output

    def test_report_with_output(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(cli, [
                "report", os.path.join(FIXTURES, "demo_repo"),
                "--output", tmpdir
            ])
            assert result.exit_code == 0
            assert os.path.exists(os.path.join(tmpdir, "callgraph.json"))
            assert os.path.exists(os.path.join(tmpdir, "callgraph.dot"))
            assert os.path.exists(os.path.join(tmpdir, "metrics.json"))
