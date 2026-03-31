"""Export call graph to JSON and DOT formats."""

import json
from typing import Optional

from .callgraph import CallGraph
from .metrics import function_metrics, repo_metrics


def to_json(graph: CallGraph) -> dict:
    """Convert call graph to the JSON format consumed by the frontend.

    This is the single contract between backend and frontend.
    """
    func_metrics = function_metrics(graph)

    nodes = []
    for qname, info in graph.functions.items():
        m = func_metrics.get(qname, {})
        nodes.append({
            "id": qname,
            "name": info.name,
            "file": info.filepath,
            "lineno": info.lineno,
            "lines": m.get("lines", info.end_lineno - info.lineno + 1),
            "complexity": m.get("complexity", 1),
            "fan_in": m.get("fan_in", 0),
            "fan_out": m.get("fan_out", 0),
            "source_code": info.source_code,
            "is_method": info.is_method,
            "class_name": info.class_name,
            "args": info.args,
            "decorators": info.decorators,
        })

    edges = [{"source": s, "target": t} for s, t in graph.edges]
    metrics = repo_metrics(graph)

    return {
        "nodes": nodes,
        "edges": edges,
        "metrics": metrics,
        "files": graph.files,
    }


def to_dot(graph: CallGraph) -> str:
    """Convert call graph to Graphviz DOT format."""
    lines = ["digraph callgraph {"]
    lines.append("    rankdir=LR;")
    lines.append('    node [shape=box, style=filled, fillcolor="#e8e8e8"];')
    lines.append("")

    file_colors = {}
    colors = [
        "#a6cee3", "#1f78b4", "#b2df8a", "#33a02c",
        "#fb9a99", "#e31a1c", "#fdbf6f", "#ff7f00",
        "#cab2d6", "#6a3d9a",
    ]
    for i, f in enumerate(graph.files):
        file_colors[f] = colors[i % len(colors)]

    for qname, info in graph.functions.items():
        color = file_colors.get(info.filepath, "#e8e8e8")
        label = info.name
        safe_id = qname.replace(".", "_")
        lines.append(f'    {safe_id} [label="{label}", fillcolor="{color}"];')

    lines.append("")

    for src, tgt in graph.edges:
        safe_src = src.replace(".", "_")
        safe_tgt = tgt.replace(".", "_")
        lines.append(f"    {safe_src} -> {safe_tgt};")

    lines.append("}")
    return "\n".join(lines)


def export_json(graph: CallGraph, output_path: str) -> None:
    """Export call graph to a JSON file."""
    data = to_json(graph)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


def export_dot(graph: CallGraph, output_path: str) -> None:
    """Export call graph to a DOT file."""
    dot = to_dot(graph)
    with open(output_path, "w") as f:
        f.write(dot)
