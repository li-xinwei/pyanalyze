"""Tests for src/parser.py — AST parsing and function extraction."""

import os
import pytest
from src.parser import parse_source, parse_file, FunctionInfo

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestParseSource:
    def test_simple_function(self):
        source = "def hello(x):\n    return x + 1\n"
        funcs = parse_source(source, "test.py", "test")
        assert "test.hello" in funcs
        info = funcs["test.hello"]
        assert info.name == "hello"
        assert info.args == ["x"]
        assert info.lineno == 1
        assert info.is_method is False

    def test_function_with_calls(self):
        source = "def process(data):\n    result = helper(data)\n    cleaned = clean(result)\n    return cleaned\n"
        funcs = parse_source(source, "test.py", "test")
        info = funcs["test.process"]
        assert "helper" in info.calls
        assert "clean" in info.calls

    def test_class_methods(self):
        source = (
            "class Foo:\n"
            "    def __init__(self, x):\n"
            "        self.x = x\n"
            "    def bar(self):\n"
            "        return self.x\n"
        )
        funcs = parse_source(source, "test.py", "test")
        assert "test.Foo.__init__" in funcs
        assert "test.Foo.bar" in funcs
        init = funcs["test.Foo.__init__"]
        assert init.is_method is True
        assert init.class_name == "Foo"

    def test_decorators(self):
        source = "@staticmethod\ndef foo():\n    pass\n"
        funcs = parse_source(source, "test.py", "test")
        info = funcs["test.foo"]
        assert "staticmethod" in info.decorators

    def test_args_with_varargs(self):
        source = "def foo(a, b, *args, **kwargs):\n    pass\n"
        funcs = parse_source(source, "test.py", "test")
        info = funcs["test.foo"]
        assert "a" in info.args
        assert "b" in info.args
        assert "*args" in info.args
        assert "**kwargs" in info.args

    def test_source_code_captured(self):
        source = "def hello(x):\n    return x + 1\n"
        funcs = parse_source(source, "test.py", "test")
        info = funcs["test.hello"]
        assert "def hello(x):" in info.source_code
        assert "return x + 1" in info.source_code

    def test_async_function(self):
        source = "async def fetch(url):\n    return await get(url)\n"
        funcs = parse_source(source, "test.py", "test")
        assert "test.fetch" in funcs
        info = funcs["test.fetch"]
        assert "get" in info.calls

    def test_attribute_calls(self):
        source = "def foo(self):\n    self.bar()\n    a.b.c()\n"
        funcs = parse_source(source, "test.py", "test")
        info = funcs["test.foo"]
        assert "self.bar" in info.calls
        assert "a.b.c" in info.calls

    def test_syntax_error_returns_empty(self):
        source = "def broken(\n"
        funcs = parse_source(source, "test.py", "test")
        assert funcs == {}

    def test_empty_function(self):
        source = "def empty():\n    pass\n"
        funcs = parse_source(source, "test.py", "test")
        assert "test.empty" in funcs

    def test_function_with_docstring_only(self):
        source = 'def documented():\n    """A docstring."""\n    pass\n'
        funcs = parse_source(source, "test.py", "test")
        assert "test.documented" in funcs

    def test_to_dict(self):
        source = "def hello(x):\n    return x + 1\n"
        funcs = parse_source(source, "test.py", "test")
        d = funcs["test.hello"].to_dict()
        assert d["name"] == "hello"
        assert d["qualified_name"] == "test.hello"
        assert isinstance(d["calls"], list)


class TestParseFile:
    def test_simple_module(self):
        filepath = os.path.join(FIXTURES, "simple_module.py")
        funcs = parse_file(filepath, FIXTURES)
        assert "simple_module.helper" in funcs
        assert "simple_module.process" in funcs
        assert "simple_module.clean" in funcs
        assert "simple_module.Processor.__init__" in funcs
        assert "simple_module.Processor.run" in funcs
        assert "simple_module.Processor.preprocess" in funcs

    def test_process_calls(self):
        filepath = os.path.join(FIXTURES, "simple_module.py")
        funcs = parse_file(filepath, FIXTURES)
        process = funcs["simple_module.process"]
        assert "helper" in process.calls
        assert "clean" in process.calls

    def test_method_calls(self):
        filepath = os.path.join(FIXTURES, "simple_module.py")
        funcs = parse_file(filepath, FIXTURES)
        run = funcs["simple_module.Processor.run"]
        assert "self.preprocess" in run.calls
        assert "process" in run.calls

    def test_module_name_from_path(self):
        filepath = os.path.join(FIXTURES, "multi_file_repo", "helpers", "math_ops.py")
        funcs = parse_file(filepath, os.path.join(FIXTURES, "multi_file_repo"))
        assert "helpers.math_ops.square" in funcs
        assert "helpers.math_ops.cube" in funcs
