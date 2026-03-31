"""Call graph construction combining parsed functions and import resolution."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

import networkx as nx

from .parser import FunctionInfo, parse_file
from .imports import build_import_map, ImportMap, _find_py_files, _filepath_to_module


@dataclass
class CallGraph:
    functions: Dict[str, FunctionInfo] = field(default_factory=dict)
    edges: List[Tuple[str, str]] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    external_calls: List[Tuple[str, str]] = field(default_factory=list)

    def get_callees(self, func_name: str) -> List[str]:
        """Functions called by func_name."""
        return [t for s, t in self.edges if s == func_name]

    def get_callers(self, func_name: str) -> List[str]:
        """Functions that call func_name."""
        return [s for s, t in self.edges if t == func_name]

    def to_networkx(self) -> nx.DiGraph:
        """Convert to NetworkX directed graph."""
        G = nx.DiGraph()
        for qname, info in self.functions.items():
            G.add_node(qname, **info.to_dict())
        for src, tgt in self.edges:
            G.add_edge(src, tgt)
        return G

    def to_dict(self) -> dict:
        return {
            "functions": {k: v.to_dict() for k, v in self.functions.items()},
            "edges": [{"source": s, "target": t} for s, t in self.edges],
            "files": self.files,
            "external_calls": [
                {"caller": c, "callee": e} for c, e in self.external_calls
            ],
        }


def _resolve_call_in_context(
    call_name: str,
    caller_info: FunctionInfo,
    file_functions: Dict[str, FunctionInfo],
    all_functions: Dict[str, FunctionInfo],
    import_map: ImportMap,
    caller_rel_path: str,
    module_name: str,
) -> Optional[str]:
    """Resolve a call name to a qualified function name."""

    if call_name.startswith("self."):
        method_name = call_name[5:]
        if caller_info.class_name:
            candidate = f"{module_name}.{caller_info.class_name}.{method_name}"
            if candidate in all_functions:
                return candidate

    if "." not in call_name:
        candidate = f"{module_name}.{call_name}"
        if candidate in all_functions:
            return candidate

        for qname in all_functions:
            if qname.endswith(f".{call_name}") and all_functions[qname].filepath == caller_info.filepath:
                return qname

    resolved = import_map.resolve(caller_rel_path, call_name.split(".")[0])
    if resolved:
        source_file, original_name = resolved
        source_module = _filepath_to_module(source_file)

        if "." in call_name:
            parts = call_name.split(".")
            attr_name = parts[-1]
            candidate = f"{source_module}.{attr_name}"
            if candidate in all_functions:
                return candidate

        candidate = f"{source_module}.{original_name}"
        if candidate in all_functions:
            return candidate

        if call_name != original_name:
            candidate = f"{source_module}.{call_name}"
            if candidate in all_functions:
                return candidate

    if "." in call_name:
        for qname in all_functions:
            if qname.endswith(f".{call_name.split('.')[-1]}"):
                parts = call_name.split(".")
                if len(parts) >= 2:
                    candidate_module = parts[0]
                    resolved_mod = import_map.resolve(caller_rel_path, candidate_module)
                    if resolved_mod:
                        src_file, _ = resolved_mod
                        src_mod = _filepath_to_module(src_file)
                        full_candidate = f"{src_mod}.{'.'.join(parts[1:])}"
                        if full_candidate in all_functions:
                            return full_candidate

    return None


def build_callgraph(repo_root: str) -> CallGraph:
    """Build a complete call graph for a Python repository."""
    graph = CallGraph()

    py_files = _find_py_files(repo_root)
    rel_files = [os.path.relpath(f, repo_root) for f in py_files]
    graph.files = sorted(rel_files)

    import_map = build_import_map(repo_root)

    all_functions: Dict[str, FunctionInfo] = {}
    file_function_map: Dict[str, Dict[str, FunctionInfo]] = {}

    for fp in py_files:
        funcs = parse_file(fp, repo_root)
        all_functions.update(funcs)
        rel = os.path.relpath(fp, repo_root)
        file_function_map[rel] = funcs

    graph.functions = all_functions

    for qname, func_info in all_functions.items():
        rel_path = func_info.filepath
        module_name = _filepath_to_module(rel_path)
        file_funcs = file_function_map.get(rel_path, {})

        for call_name in func_info.calls:
            resolved = _resolve_call_in_context(
                call_name, func_info, file_funcs, all_functions,
                import_map, rel_path, module_name,
            )

            if resolved:
                edge = (qname, resolved)
                if edge not in graph.edges:
                    graph.edges.append(edge)
            else:
                graph.external_calls.append((qname, call_name))

    return graph
