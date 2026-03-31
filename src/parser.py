"""AST parsing and function/class extraction for Python source files."""

import ast
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class FunctionInfo:
    name: str
    qualified_name: str
    filepath: str
    lineno: int
    end_lineno: int
    calls: List[str] = field(default_factory=list)
    args: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    is_method: bool = False
    class_name: Optional[str] = None
    global_refs: List[str] = field(default_factory=list)
    source_code: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "qualified_name": self.qualified_name,
            "filepath": self.filepath,
            "lineno": self.lineno,
            "end_lineno": self.end_lineno,
            "calls": self.calls,
            "args": self.args,
            "decorators": self.decorators,
            "is_method": self.is_method,
            "class_name": self.class_name,
            "global_refs": self.global_refs,
            "source_code": self.source_code,
        }


def _resolve_call_name(node: ast.expr) -> Optional[str]:
    """Resolve a Call node's function expression to a dotted name string."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        value = _resolve_call_name(node.value)
        if value is not None:
            return f"{value}.{node.attr}"
        return node.attr
    return None


def _extract_calls(body_nodes) -> List[str]:
    """Walk AST nodes and extract all function call names."""
    calls = []
    for node in ast.walk(ast.Module(body=list(body_nodes), type_ignores=[])):
        if isinstance(node, ast.Call):
            name = _resolve_call_name(node.func)
            if name and name not in calls:
                calls.append(name)
    return calls


def _extract_decorator_names(decorator_list) -> List[str]:
    names = []
    for dec in decorator_list:
        name = _resolve_call_name(dec) if isinstance(dec, (ast.Name, ast.Attribute)) else None
        if name is None and isinstance(dec, ast.Call):
            name = _resolve_call_name(dec.func)
        if name:
            names.append(name)
    return names


def _extract_args(arguments: ast.arguments) -> List[str]:
    args = [a.arg for a in arguments.args]
    if arguments.vararg:
        args.append(f"*{arguments.vararg.arg}")
    if arguments.kwarg:
        args.append(f"**{arguments.kwarg.arg}")
    return args


def _get_source_segment(source: str, node: ast.AST) -> str:
    """Extract source code for a node using line numbers."""
    lines = source.splitlines()
    start = node.lineno - 1
    end = node.end_lineno if node.end_lineno else node.lineno
    return "\n".join(lines[start:end])


def _extract_global_refs(func_node: ast.FunctionDef, local_names: set) -> List[str]:
    """Find Name references that aren't local variables or parameters."""
    refs = []
    local = set(local_names)
    for a in func_node.args.args:
        local.add(a.arg)
    if func_node.args.vararg:
        local.add(func_node.args.vararg.arg)
    if func_node.args.kwarg:
        local.add(func_node.args.kwarg.arg)

    for node in ast.walk(func_node):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id not in local and node.id not in refs:
                builtin_names = {
                    'print', 'len', 'range', 'str', 'int', 'float', 'list',
                    'dict', 'set', 'tuple', 'bool', 'None', 'True', 'False',
                    'isinstance', 'type', 'super', 'enumerate', 'zip', 'map',
                    'filter', 'sorted', 'reversed', 'any', 'all', 'sum',
                    'min', 'max', 'abs', 'open', 'hasattr', 'getattr',
                    'setattr', 'ValueError', 'TypeError', 'Exception',
                    'KeyError', 'IndexError', 'AttributeError', 'RuntimeError',
                    'NotImplementedError', 'StopIteration', 'OSError',
                }
                if node.id not in builtin_names:
                    refs.append(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node is not func_node:
                local.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    local.add(target.id)
        elif isinstance(node, ast.For):
            if isinstance(node.target, ast.Name):
                local.add(node.target.id)
        elif isinstance(node, ast.comprehension):
            if isinstance(node.target, ast.Name):
                local.add(node.target.id)

    return refs


class _FunctionVisitor(ast.NodeVisitor):
    """Visit AST and extract FunctionInfo for all functions and methods."""

    def __init__(self, source: str, filepath: str, module_name: str):
        self.source = source
        self.filepath = filepath
        self.module_name = module_name
        self.functions: Dict[str, FunctionInfo] = {}
        self._class_stack: List[str] = []

    def _make_qualified_name(self, name: str) -> str:
        parts = [self.module_name]
        parts.extend(self._class_stack)
        parts.append(name)
        return ".".join(parts)

    def _process_function(self, node, is_async=False):
        qualified = self._make_qualified_name(node.name)
        calls = _extract_calls(node.body)
        args = _extract_args(node.args)
        decorators = _extract_decorator_names(node.decorator_list)
        is_method = len(self._class_stack) > 0
        class_name = self._class_stack[-1] if is_method else None
        source_code = _get_source_segment(self.source, node)
        global_refs = _extract_global_refs(node, set())

        info = FunctionInfo(
            name=node.name,
            qualified_name=qualified,
            filepath=self.filepath,
            lineno=node.lineno,
            end_lineno=node.end_lineno or node.lineno,
            calls=calls,
            args=args,
            decorators=decorators,
            is_method=is_method,
            class_name=class_name,
            global_refs=global_refs,
            source_code=source_code,
        )
        self.functions[qualified] = info

        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._class_stack.append(node.name)
                self._process_function(child)
                self._class_stack.pop()

    def visit_FunctionDef(self, node):
        self._process_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._process_function(node, is_async=True)

    def visit_ClassDef(self, node):
        self._class_stack.append(node.name)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._process_function(child)
        self._class_stack.pop()


def parse_source(source: str, filepath: str = "<string>",
                 module_name: str = "<module>") -> Dict[str, FunctionInfo]:
    """Parse Python source code and extract all function definitions."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    visitor = _FunctionVisitor(source, filepath, module_name)
    visitor.visit(tree)
    return visitor.functions


def parse_file(filepath: str, repo_root: str = "") -> Dict[str, FunctionInfo]:
    """Parse a Python file and extract function info.

    The module_name is derived from the filepath relative to repo_root.
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()

    if repo_root:
        rel = os.path.relpath(filepath, repo_root)
    else:
        rel = os.path.basename(filepath)

    module_name = rel.replace(os.sep, ".").replace("/", ".")
    if module_name.endswith(".py"):
        module_name = module_name[:-3]
    if module_name.endswith(".__init__"):
        module_name = module_name[:-9]

    return parse_source(source, filepath=rel, module_name=module_name)
