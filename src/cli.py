"""Command-line interface using Click."""

import json
import click

from .callgraph import build_callgraph
from .slicer import backward_slice
from .export import export_json, export_dot, to_json
from .metrics import repo_metrics


@click.group()
def cli():
    """PyAnalyze — Python Static Analysis Tool."""
    pass


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True))
@click.option("--output", "-o", default=None, help="Output file path (JSON)")
@click.option("--format", "fmt", type=click.Choice(["json", "dot"]),
              default="json", help="Output format")
def analyze(repo_path, output, fmt):
    """Analyze a Python repository and generate a call graph."""
    click.echo(f"Analyzing {repo_path}...")
    graph = build_callgraph(repo_path)

    metrics = repo_metrics(graph)
    click.echo(f"  Files: {metrics['total_files']}")
    click.echo(f"  Functions: {metrics['total_functions']}")
    click.echo(f"  Edges: {metrics['total_edges']}")
    click.echo(f"  Avg Complexity: {metrics['avg_complexity']}")
    click.echo(f"  Avg Slice Reduction: {metrics['avg_slice_reduction']:.1%}")

    if output:
        if fmt == "dot":
            export_dot(graph, output)
        else:
            export_json(graph, output)
        click.echo(f"Output written to {output}")
    else:
        result = to_json(graph)
        click.echo(json.dumps(result, indent=2))


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True))
@click.option("--target", "-t", required=True, help="Target function (qualified name)")
@click.option("--output", "-o", default=None, help="Output file path")
@click.option("--max-depth", "-d", default=-1, type=int, help="Max traversal depth")
def slice(repo_path, target, output, max_depth):
    """Compute backward slice for a target function."""
    click.echo(f"Building call graph for {repo_path}...")
    graph = build_callgraph(repo_path)

    click.echo(f"Computing slice for {target}...")
    result = backward_slice(graph, target, max_depth=max_depth)

    click.echo(f"  Dependencies: {len(result.dependencies)}")
    click.echo(f"  Slice lines: {result.total_lines}")
    click.echo(f"  Original lines: {result.original_lines}")
    click.echo(f"  Reduction: {result.reduction_ratio:.1%}")

    data = result.to_dict()
    if output:
        with open(output, "w") as f:
            json.dump(data, f, indent=2)
        click.echo(f"Output written to {output}")
    else:
        click.echo(json.dumps(data, indent=2))


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True))
@click.option("--output", "-o", default=None, help="Output directory for report")
def report(repo_path, output):
    """Generate a full analysis report."""
    click.echo(f"Analyzing {repo_path}...")
    graph = build_callgraph(repo_path)
    metrics = repo_metrics(graph)

    click.echo("\n=== Repository Report ===")
    click.echo(f"Files: {metrics['total_files']}")
    click.echo(f"Functions: {metrics['total_functions']}")
    click.echo(f"Call edges: {metrics['total_edges']}")
    click.echo(f"Avg cyclomatic complexity: {metrics['avg_complexity']}")
    click.echo(f"Max fan-in: {metrics['max_fan_in']}")
    click.echo(f"Max fan-out: {metrics['max_fan_out']}")
    click.echo(f"Avg slice reduction: {metrics['avg_slice_reduction']:.1%}")

    if output:
        import os
        os.makedirs(output, exist_ok=True)
        export_json(graph, os.path.join(output, "callgraph.json"))
        export_dot(graph, os.path.join(output, "callgraph.dot"))

        with open(os.path.join(output, "metrics.json"), "w") as f:
            json.dump(metrics, f, indent=2)

        click.echo(f"\nReport written to {output}/")


if __name__ == "__main__":
    cli()
