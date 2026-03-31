"""Backward slicing algorithm for computing minimal code context."""

from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional

from .callgraph import CallGraph


@dataclass
class Slice:
    target: str
    dependencies: List[str] = field(default_factory=list)
    global_vars: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    total_lines: int = 0
    original_lines: int = 0
    reduction_ratio: float = 0.0
    code: str = ""

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "dependencies": self.dependencies,
            "global_vars": self.global_vars,
            "imports": self.imports,
            "total_lines": self.total_lines,
            "original_lines": self.original_lines,
            "reduction_ratio": round(self.reduction_ratio, 4),
            "code": self.code,
        }


def _topological_sort(func_names: set, graph: CallGraph) -> List[str]:
    """Topologically sort functions so dependencies come before dependents."""
    in_slice = func_names.copy()
    in_degree = {f: 0 for f in in_slice}

    for src, tgt in graph.edges:
        if src in in_slice and tgt in in_slice:
            in_degree[src] = in_degree.get(src, 0) + 1

    queue = deque([f for f in in_slice if in_degree.get(f, 0) == 0])
    result = []

    while queue:
        node = queue.popleft()
        result.append(node)
        for src, tgt in graph.edges:
            if tgt == node and src in in_slice:
                in_degree[src] -= 1
                if in_degree[src] == 0:
                    queue.append(src)

    remaining = [f for f in in_slice if f not in result]
    result.extend(remaining)

    return result


def backward_slice(graph: CallGraph, target: str,
                   max_depth: int = -1) -> Slice:
    """Compute backward slice for target function.

    BFS through the call graph following callee edges to collect all
    transitive dependencies. Handles cycles without infinite loops
    via a visited set.
    """
    if target not in graph.functions:
        candidates = [
            qn for qn in graph.functions
            if qn.endswith(f".{target}") or qn == target
        ]
        if candidates:
            target = candidates[0]
        else:
            return Slice(target=target)

    visited = set()
    queue = deque([(target, 0)])

    while queue:
        current, depth = queue.popleft()
        if current in visited:
            continue
        visited.add(current)

        if 0 <= max_depth <= depth:
            continue

        if current in graph.functions:
            callees = graph.get_callees(current)
            for callee in callees:
                if callee not in visited and callee in graph.functions:
                    queue.append((callee, depth + 1))

    sorted_funcs = _topological_sort(visited, graph)

    all_global_vars = []
    all_imports = set()
    code_parts = []

    for func_name in sorted_funcs:
        if func_name in graph.functions:
            info = graph.functions[func_name]
            code_parts.append(info.source_code)
            for ref in info.global_refs:
                if ref not in all_global_vars:
                    all_global_vars.append(ref)

    code = "\n\n".join(code_parts)

    slice_lines = sum(
        info.end_lineno - info.lineno + 1
        for info in graph.functions.values()
        if info.qualified_name in visited
    )
    total_lines = sum(
        info.end_lineno - info.lineno + 1
        for info in graph.functions.values()
    )
    reduction = 1 - (slice_lines / total_lines) if total_lines > 0 else 0.0

    return Slice(
        target=target,
        dependencies=sorted_funcs,
        global_vars=all_global_vars,
        imports=sorted(all_imports),
        total_lines=slice_lines,
        original_lines=total_lines,
        reduction_ratio=reduction,
        code=code,
    )
