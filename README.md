# PyAnalyze

A static analysis tool for Python that extracts call graphs,
computes backward slices, and visualizes dependencies.

## Features

- AST-based function extraction across multi-file repos
- Cross-file import resolution
- Backward slicing for minimal code context
- Cyclomatic complexity analysis
- Interactive D3.js visualization
- REST API for programmatic access
- CLI for batch analysis

## Quick Start

### CLI

```bash
pip install -r requirements.txt

# Analyze a repo
python -m src.cli analyze /path/to/repo --output graph.json

# Compute backward slice
python -m src.cli slice /path/to/repo --target "module.func_name" --output slice.json

# Full report
python -m src.cli report /path/to/repo --output report/
```

### API

```bash
cd api
pip install -r requirements.txt
flask run --port 8000
```

Endpoints:
- `POST /api/analyze` — Analyze uploaded Python files
- `POST /api/slice` — Compute backward slice for a target function
- `GET /api/demo` — Get pre-computed demo analysis
- `GET /api/health` — Health check

### Web Frontend

```bash
cd web
npm install
npm run dev
```

## Architecture

```
src/parser.py     → AST parsing, function extraction
src/imports.py    → Cross-file import resolution
src/callgraph.py  → Call graph construction (NetworkX)
src/slicer.py     → Backward slicing algorithm
src/metrics.py    → Cyclomatic complexity metrics
src/export.py     → JSON/DOT export
src/cli.py        → Click CLI

api/app.py        → Flask REST API
web/              → React + D3.js frontend
```

## Tests

```bash
pytest tests/ -v
```

## Benchmarks

```bash
python benchmarks/run_benchmarks.py
```
