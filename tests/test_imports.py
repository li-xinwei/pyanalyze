"""Tests for src/imports.py — Cross-file import resolution."""

import os
import pytest
from src.imports import build_import_map, _extract_imports, _filepath_to_module

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestExtractImports:
    def test_simple_import(self):
        source = "import os\n"
        imports = _extract_imports(source)
        assert len(imports) >= 1
        assert any(i["name"] == "os" for i in imports)

    def test_from_import(self):
        source = "from utils import validate\n"
        imports = _extract_imports(source)
        assert any(i["name"] == "validate" and i["module"] == "utils" for i in imports)

    def test_from_import_with_alias(self):
        source = "from utils import validate as v\n"
        imports = _extract_imports(source)
        assert any(i["alias"] == "v" and i["name"] == "validate" for i in imports)

    def test_dotted_import(self):
        source = "from helpers.math_ops import square\n"
        imports = _extract_imports(source)
        assert any(
            i["name"] == "square" and i["module"] == "helpers.math_ops"
            for i in imports
        )

    def test_syntax_error(self):
        source = "from import\n"
        imports = _extract_imports(source)
        assert imports == []


class TestFilepathToModule:
    def test_simple(self):
        assert _filepath_to_module("main.py") == "main"

    def test_nested(self):
        assert _filepath_to_module("helpers/math_ops.py") == "helpers.math_ops"

    def test_init(self):
        assert _filepath_to_module("helpers/__init__.py") == "helpers"


class TestBuildImportMap:
    def test_multi_file_repo(self):
        repo = os.path.join(FIXTURES, "multi_file_repo")
        imap = build_import_map(repo)

        result = imap.resolve("main.py", "validate")
        assert result is not None
        source_file, original_name = result
        assert "utils" in source_file
        assert original_name == "validate"

    def test_dotted_import_resolution(self):
        repo = os.path.join(FIXTURES, "multi_file_repo")
        imap = build_import_map(repo)

        result = imap.resolve("main.py", "square")
        assert result is not None
        source_file, original_name = result
        assert "math_ops" in source_file
        assert original_name == "square"

    def test_demo_repo_imports(self):
        repo = os.path.join(FIXTURES, "demo_repo")
        imap = build_import_map(repo)

        result = imap.resolve("scraper.py", "extract_links")
        assert result is not None
        source_file, original_name = result
        assert "parser" in source_file

    def test_unresolved_import_returns_none(self):
        repo = os.path.join(FIXTURES, "multi_file_repo")
        imap = build_import_map(repo)
        result = imap.resolve("main.py", "nonexistent_func")
        assert result is None
