"""Run benchmarks on real-world Python repositories."""

import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.callgraph import build_callgraph
from src.metrics import repo_metrics


def clone_repo(url, dest):
    """Clone a git repo if not already present."""
    if os.path.isdir(dest):
        return True
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", url, dest],
            check=True, capture_output=True, timeout=120
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def find_python_source_dir(repo_dir):
    """Find the main source directory in a repo."""
    candidates = ["src", "lib", repo_dir]
    for name in os.listdir(repo_dir):
        full = os.path.join(repo_dir, name)
        if os.path.isdir(full) and not name.startswith("."):
            py_files = []
            for r, _, files in os.walk(full):
                py_files.extend(f for f in files if f.endswith(".py"))
            if len(py_files) > 5:
                return full
    return repo_dir


def run_benchmark(name, url, repos_dir):
    """Run benchmark on a single repo."""
    dest = os.path.join(repos_dir, name)
    print(f"  Cloning {name}...", end=" ", flush=True)

    if not clone_repo(url, dest):
        print("FAILED")
        return None

    source_dir = find_python_source_dir(dest)
    print(f"Analyzing {source_dir}...", end=" ", flush=True)

    start = time.time()
    try:
        graph = build_callgraph(source_dir)
        m = repo_metrics(graph)
        elapsed = time.time() - start
        m["name"] = name
        m["time_seconds"] = round(elapsed, 2)
        print(f"OK ({elapsed:.1f}s)")
        return m
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repos_file = os.path.join(script_dir, "repos.json")
    repos_dir = os.path.join(script_dir, "repos")
    results_dir = os.path.join(script_dir, "results")

    os.makedirs(repos_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    with open(repos_file) as f:
        repos = json.load(f)

    print(f"Running benchmarks on {len(repos)} repositories...\n")

    results = []
    for repo in repos:
        m = run_benchmark(repo["name"], repo["url"], repos_dir)
        if m:
            results.append(m)

    with open(os.path.join(results_dir, "benchmark_results.json"), "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print(f"{'Repo':<12} {'Files':>6} {'Functions':>10} {'Edges':>7} "
          f"{'Avg Slice Red':>14} {'Avg CC':>7} {'Time':>6}")
    print("-" * 80)

    totals = {"files": 0, "functions": 0, "edges": 0, "slice": 0, "cc": 0}
    for m in results:
        print(f"{m['name']:<12} {m['total_files']:>6} {m['total_functions']:>10} "
              f"{m['total_edges']:>7} {m['avg_slice_reduction']:>13.1%} "
              f"{m['avg_complexity']:>7.1f} {m.get('time_seconds', 0):>5.1f}s")
        totals["files"] += m["total_files"]
        totals["functions"] += m["total_functions"]
        totals["edges"] += m["total_edges"]
        totals["slice"] += m["avg_slice_reduction"]
        totals["cc"] += m["avg_complexity"]

    n = len(results) or 1
    print("-" * 80)
    print(f"{'AVERAGE':<12} {totals['files']/n:>6.0f} {totals['functions']/n:>10.0f} "
          f"{totals['edges']/n:>7.0f} {totals['slice']/n:>13.1%} "
          f"{totals['cc']/n:>7.1f}")
    print("=" * 80)


if __name__ == "__main__":
    main()
