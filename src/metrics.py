"""Cyclomatic complexity and other code metrics."""

import ast
from typing import Dict

from .callgraph import CallGraph
from .slicer import backward_slice


def cyclomatic_complexity(func_node: ast.AST) -> int:
    """Compute cyclomatic complexity for a function AST node.

    CC = 1 + number of decision points (if, elif, for, while, except,
    and, or, assert, with, ternary IfExp).
    """
    complexity = 1
    for node in ast.walk(func_node):
        if isinstance(node, (ast.If, ast.For, ast.While,
                             ast.ExceptHandler, ast.With,
                             ast.Assert, ast.IfExp)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
    return complexity


def compute_complexity_from_source(source_code: str) -> int:
    """Compute cyclomatic complexity from a function's source code string."""
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return 1

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cyclomatic_complexity(node)
    return 1


def function_metrics(graph: CallGraph) -> Dict[str, dict]:
    """Compute per-function metrics."""
    metrics = {}
    for qname, info in graph.functions.items():
        cc = compute_complexity_from_source(info.source_code)
        fan_in = len(graph.get_callers(qname))
        fan_out = len(graph.get_callees(qname))
        lines = info.end_lineno - info.lineno + 1

        metrics[qname] = {
            "complexity": cc,
            "fan_in": fan_in,
            "fan_out": fan_out,
            "lines": lines,
        }
    return metrics


def repo_metrics(graph: CallGraph) -> dict:
    """Aggregate metrics for the whole repository."""
    func_metrics = function_metrics(graph)

    complexities = [m["complexity"] for m in func_metrics.values()]
    fan_ins = [m["fan_in"] for m in func_metrics.values()]
    fan_outs = [m["fan_out"] for m in func_metrics.values()]

    avg_cc = sum(complexities) / len(complexities) if complexities else 0

    slice_reductions = []
    for qname in graph.functions:
        try:
            s = backward_slice(graph, qname)
            slice_reductions.append(s.reduction_ratio)
        except Exception:
            pass

    avg_slice = (sum(slice_reductions) / len(slice_reductions)
                 if slice_reductions else 0)

    return {
        "total_files": len(graph.files),
        "total_functions": len(graph.functions),
        "total_edges": len(graph.edges),
        "avg_complexity": round(avg_cc, 2),
        "avg_slice_reduction": round(avg_slice, 4),
        "max_fan_in": max(fan_ins) if fan_ins else 0,
        "max_fan_out": max(fan_outs) if fan_outs else 0,
    }
