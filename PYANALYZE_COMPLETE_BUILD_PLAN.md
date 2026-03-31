# PyAnalyze — Python Static Analysis & Dependency Visualization
## Complete Build Plan (CLI + Web App)

---

## Project Overview

Build a Python static analysis tool that parses source code into ASTs, extracts function-level call graphs and module dependency structures across multi-file repositories, computes backward slices for minimal code context, and visualizes everything through an interactive web interface.

The end product is a **live web demo** hosted on your personal website where visitors can paste Python code, see an interactive call graph, click any function to see its backward slice, and explore dependency metrics — all in real time.

This is a REAL project that must produce working code, real metrics on real repositories, and a deployable web app. Someone should be able to visit the URL, interact with it immediately (pre-loaded demo), and be impressed.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React + D3.js)              │
│                    Deployed on Vercel                    │
│                                                         │
│  ┌──────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │Code Input│  │ D3.js Call Graph  │  │ Metrics Panel │  │
│  │(paste/   │──│ (force-directed,  │──│ (complexity,  │  │
│  │ upload)  │  │  interactive)     │  │  slice ratio) │  │
│  └──────────┘  └──────────────────┘  └───────────────┘  │
│                         │                                │
│  ┌──────────────────────┴────────────────────────────┐   │
│  │           Slice View (highlighted code)            │   │
│  └───────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP (JSON)
┌─────────────────────────┴───────────────────────────────┐
│                    Backend (Flask API)                    │
│                    Deployed on Render                     │
│                                                          │
│  ┌──────────┐  ┌───────────┐  ┌────────┐  ┌──────────┐  │
│  │ Parser   │──│ CallGraph │──│ Slicer │──│ Metrics  │  │
│  │ (AST)    │  │ Builder   │  │        │  │          │  │
│  └──────────┘  └───────────┘  └────────┘  └──────────┘  │
│       │                                                  │
│  ┌────┴─────┐                                            │
│  │ Import   │                                            │
│  │ Resolver │                                            │
│  └──────────┘                                            │
└──────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
pyanalyze/
├── README.md
├── pyproject.toml
├── requirements.txt           # networkx, click, rich, pytest, pytest-cov
│
├── src/                       # Core analysis engine
│   ├── __init__.py
│   ├── parser.py              # AST parsing and function/class extraction
│   ├── callgraph.py           # Call graph construction (intra + cross-file)
│   ├── imports.py             # Import resolution across multi-file repos
│   ├── slicer.py              # Backward slicing algorithm
│   ├── metrics.py             # Cyclomatic complexity and other metrics
│   ├── export.py              # Export to JSON, DOT (graphviz), summary
│   └── cli.py                 # Command-line interface using Click
│
├── api/                       # Flask API backend
│   ├── app.py                 # Flask server wrapping src/ pipeline
│   ├── requirements.txt       # flask, flask-cors, gunicorn
│   ├── Dockerfile
│   └── render.yaml            # Render deployment config
│
├── web/                       # React frontend
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── App.jsx
│       ├── index.jsx
│       ├── demo/
│       │   └── demo_result.json       # Pre-computed demo data
│       ├── components/
│       │   ├── CodeInput.jsx          # Code paste / file upload
│       │   ├── CallGraph.jsx          # D3.js force-directed graph
│       │   ├── SliceView.jsx          # Backward slice display
│       │   ├── MetricsPanel.jsx       # Stats sidebar
│       │   ├── FunctionList.jsx       # Clickable function list
│       │   └── ExportButton.jsx       # Download JSON / PNG
│       ├── hooks/
│       │   └── useAnalysis.js         # API call hook
│       └── utils/
│           └── graphLayout.js         # D3 force simulation config
│
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_callgraph.py
│   ├── test_imports.py
│   ├── test_slicer.py
│   ├── test_metrics.py
│   └── fixtures/                      # Test repos
│       ├── simple_module.py
│       ├── multi_file_repo/
│       │   ├── main.py
│       │   ├── utils.py
│       │   └── helpers/
│       │       ├── __init__.py
│       │       └── math_ops.py
│       └── demo_repo/                 # Also used as web demo
│           ├── scraper.py
│           ├── parser.py
│           ├── storage.py
│           ├── config.py
│           └── utils.py
│
└── benchmarks/
    ├── run_benchmarks.py
    ├── repos.json
    └── results/
```

---

## Phase 1: Core AST Parsing (Day 1 Morning — 3h)

### File: `src/parser.py`

**Goal:** Parse a single Python file and extract all function definitions, class definitions, and their relationships.

**Data structures:**

```python
@dataclass
class FunctionInfo:
    name: str                    # Function name
    qualified_name: str          # module.ClassName.func_name
    filepath: str                # Source file path
    lineno: int                  # Start line number
    end_lineno: int              # End line number
    calls: List[str]             # List of function names called within this function
    args: List[str]              # Parameter names
    decorators: List[str]        # Decorator names
    is_method: bool              # Whether it's a class method
    class_name: Optional[str]    # Parent class name if method
    global_refs: List[str]       # Global variables referenced
    source_code: str             # Raw source code of the function
```

**Implementation steps:**

1. Use `ast.parse(source_code)` to get the AST
2. Walk the AST with `ast.NodeVisitor` subclass
3. For each `ast.FunctionDef` and `ast.AsyncFunctionDef`:
   - Record name, line numbers, arguments
   - Use `ast.get_source_segment()` to capture raw source code
   - Walk the function body to find all `ast.Call` nodes
   - For each `ast.Call`, resolve the function name:
     - Simple call: `foo()` → "foo"
     - Attribute call: `self.foo()` → "self.foo"
     - Chained call: `a.b.c()` → "a.b.c"
   - Record global variable references (`ast.Name` nodes that aren't local)
4. For each `ast.ClassDef`:
   - Record methods as FunctionInfo with `is_method=True`
   - Track inheritance (base classes)

**Edge cases to handle:**
- Lambda functions (ignore for now)
- Nested function definitions (include with qualified name like `outer.inner`)
- Decorators (record names)
- `*args` and `**kwargs` in arguments
- Comprehensions and generator expressions containing calls

**Test fixture `tests/fixtures/simple_module.py`:**
```python
import os
from pathlib import Path

GLOBAL_VAR = 42

def helper(x):
    return x * 2

def process(data):
    result = helper(data)
    cleaned = clean(result)
    return cleaned

def clean(value):
    return str(value).strip()

class Processor:
    def __init__(self, config):
        self.config = config

    def run(self, data):
        intermediate = self.preprocess(data)
        return process(intermediate)

    def preprocess(self, data):
        return helper(data)
```

**Expected output for `process` function:**
```json
{
    "name": "process",
    "qualified_name": "simple_module.process",
    "filepath": "simple_module.py",
    "lineno": 9,
    "calls": ["helper", "clean"],
    "args": ["data"],
    "is_method": false
}
```

---

## Phase 2: Cross-File Import Resolution (Day 1 Afternoon — 3h)

### File: `src/imports.py`

**Goal:** Given a repository root, resolve all imports to map symbol names to their source file and function.

**Implementation:**

1. Walk the repo directory tree, find all `.py` files
2. For each file, extract all import statements:
   - `import foo` → maps "foo" to the module
   - `from foo import bar` → maps "bar" to foo.bar
   - `from foo.bar import baz` → maps "baz" to foo.bar.baz
   - `from . import foo` → relative import resolution
3. Build a global symbol table:
   ```python
   @dataclass
   class ImportMap:
       # Maps (filepath, local_name) → (source_filepath, original_name)
       symbol_map: Dict[Tuple[str, str], Tuple[str, str]]
   ```
4. Handle relative imports by computing package structure from directory layout
5. Handle `__init__.py` re-exports

**Test fixture `tests/fixtures/multi_file_repo/`:**

`main.py`:
```python
from utils import validate
from helpers.math_ops import square

def main():
    data = validate("input")
    result = square(data)
    return result
```

`utils.py`:
```python
def validate(x):
    if not x:
        raise ValueError("empty")
    return x

def format_output(x):
    return f"Result: {x}"
```

`helpers/math_ops.py`:
```python
def square(x):
    return x ** 2

def cube(x):
    return x ** 3
```

---

## Phase 3: Call Graph Construction (Day 1 Evening — 3h)

### File: `src/callgraph.py`

**Goal:** Combine parsed functions + import resolution to build a complete call graph for an entire repository.

```python
@dataclass
class CallGraph:
    functions: Dict[str, FunctionInfo]       # qualified_name → FunctionInfo
    edges: List[Tuple[str, str]]             # (caller_qualified, callee_qualified)
    files: List[str]                         # All files in repo
    external_calls: List[Tuple[str, str]]    # (caller, unresolved_callee)

    def get_callees(self, func_name: str) -> List[str]:
        """Functions called by func_name"""

    def get_callers(self, func_name: str) -> List[str]:
        """Functions that call func_name"""

    def to_networkx(self) -> nx.DiGraph:
        """Convert to NetworkX directed graph"""

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict for API/export"""
```

**Steps:**
1. Parse all `.py` files in repo → get all FunctionInfo objects
2. Build import map
3. For each function, resolve its `calls` list:
   - If call target is a local function in same file → direct edge
   - If call target matches an import → resolve via import map → cross-file edge
   - If call target is `self.method` → resolve to method in same class
   - If call target is unresolved → store in external_calls (don't crash)
4. Store as directed graph using NetworkX

**Important: Don't crash on unresolved calls.** Many calls will be to stdlib or third-party libraries. Log them but don't fail.

---

## Phase 4: Backward Slicing (Day 2 Morning — 3h) ⭐ MOST IMPORTANT

### File: `src/slicer.py`

**Goal:** Given a target function, compute the minimal set of code needed to understand it.

**This is the core algorithm that maps to R2E's dependency slicing approach and the key selling point of the project.**

```python
@dataclass
class Slice:
    target: str                          # Target function qualified name
    dependencies: List[str]              # All functions in the slice (topo-sorted)
    global_vars: List[str]               # Global variables needed
    imports: List[str]                   # Import statements needed
    total_lines: int                     # Total LOC in slice
    original_lines: int                  # Total LOC in full file/repo
    reduction_ratio: float               # 1 - (total_lines / original_lines)
    code: str                            # Concatenated minimal source code

    def to_dict(self) -> dict:
        """JSON-serializable output for API"""

def backward_slice(graph: CallGraph, target: str, max_depth: int = -1) -> Slice:
    """
    Compute backward slice for target function.

    Algorithm:
    1. Start with target function
    2. BFS through call graph following callee edges
    3. Collect all reachable functions (transitive dependencies)
    4. For each collected function, also collect:
       - Global variables referenced
       - Import statements needed
    5. Topologically sort the result (dependencies before dependents)
    6. Concatenate source code of all functions in order
    7. Compute reduction ratio

    max_depth: limit traversal depth (-1 for unlimited)
    """
```

**Algorithm pseudocode:**
```
function backward_slice(target):
    visited = set()
    queue = [target]

    while queue not empty:
        current = queue.pop(0)
        if current in visited: continue
        visited.add(current)

        func_info = graph.functions[current]
        for callee in func_info.calls:
            resolved = resolve_call(callee)  # use import map
            if resolved in graph.functions:  # only internal functions
                queue.append(resolved)

    # Topologically sort visited functions
    sorted_funcs = topological_sort(visited, graph)

    # Concatenate source code
    code_parts = []
    for func_name in sorted_funcs:
        code_parts.append(graph.functions[func_name].source_code)
    code = "\n\n".join(code_parts)

    # Compute metrics
    slice_lines = sum(
        f.end_lineno - f.lineno + 1
        for f in graph.functions.values()
        if f.qualified_name in visited
    )
    total_lines = sum(
        f.end_lineno - f.lineno + 1
        for f in graph.functions.values()
    )
    reduction = 1 - (slice_lines / total_lines) if total_lines > 0 else 0

    return Slice(target, sorted_funcs, ..., reduction, code)
```

---

## Phase 5: Metrics (Day 2 Afternoon — 2h)

### File: `src/metrics.py`

```python
def cyclomatic_complexity(func_node: ast.FunctionDef) -> int:
    """
    CC = 1 + number of decision points
    Decision points: if, elif, for, while, except, and, or,
                     assert, with, ternary (IfExp)
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

def repo_metrics(graph: CallGraph) -> dict:
    """Aggregate metrics for the whole repo"""
    return {
        "total_files": len(graph.files),
        "total_functions": len(graph.functions),
        "total_edges": len(graph.edges),
        "avg_complexity": mean([...]),
        "avg_slice_reduction": mean([...]),  # average over all functions
        "max_fan_in": ...,
        "max_fan_out": ...,
    }
```

---

## Phase 6: Export & CLI (Day 2 Afternoon — 2h)

### File: `src/export.py`

Export call graph in JSON format (primary, used by web app) and DOT format (for Graphviz):

**JSON format (this is the contract between backend and frontend):**
```json
{
    "nodes": [
        {
            "id": "main.main",
            "name": "main",
            "file": "main.py",
            "lineno": 5,
            "lines": 4,
            "complexity": 2,
            "fan_in": 0,
            "fan_out": 2,
            "source_code": "def main():\n    ..."
        }
    ],
    "edges": [
        {"source": "main.main", "target": "utils.validate"},
        {"source": "main.main", "target": "helpers.math_ops.square"}
    ],
    "metrics": {
        "total_files": 4,
        "total_functions": 12,
        "total_edges": 15,
        "avg_complexity": 3.2,
        "avg_slice_reduction": 0.54
    },
    "files": ["main.py", "utils.py", "helpers/math_ops.py"]
}
```

### File: `src/cli.py`

```
$ pyanalyze analyze /path/to/repo --output callgraph.json
$ pyanalyze slice /path/to/repo --target "main.process" --output slice.json
$ pyanalyze report /path/to/repo --output report/
```

---

## Phase 7: Flask API Backend (Day 3 Morning — 3h)

### File: `api/app.py`

**The API is a thin wrapper around the existing `src/` pipeline. Do NOT rewrite any analysis logic here.**

**Endpoints:**

```
POST /api/analyze
    Body: { "files": [{"name": "main.py", "content": "..."}, ...] }
    Returns: Full call graph JSON (same format as export.py)

POST /api/slice
    Body: { "files": [...], "target": "module.func_name" }
    Returns: {
        "slice": {
            "target": "module.func_name",
            "dependencies": [...],
            "code": "... minimal code context ...",
            "reduction_ratio": 0.55,
            "total_lines": 12,
            "original_lines": 27
        }
    }

GET /api/health
    Returns: { "status": "ok" }

GET /api/demo
    Returns: Pre-computed analysis of bundled demo repo
```

**Implementation:**

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile, os, shutil

from src.parser import parse_file
from src.callgraph import build_callgraph
from src.slicer import backward_slice
from src.export import to_json

app = Flask(__name__)
CORS(app)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    files = data.get('files', [])

    tmpdir = tempfile.mkdtemp()
    try:
        for f in files:
            filepath = os.path.join(tmpdir, f['name'])
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as fh:
                fh.write(f['content'])

        graph = build_callgraph(tmpdir)
        result = to_json(graph)
        return jsonify(result)
    finally:
        shutil.rmtree(tmpdir)

@app.route('/api/slice', methods=['POST'])
def slice_endpoint():
    data = request.json
    files = data.get('files', [])
    target = data.get('target', '')

    tmpdir = tempfile.mkdtemp()
    try:
        for f in files:
            filepath = os.path.join(tmpdir, f['name'])
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as fh:
                fh.write(f['content'])

        graph = build_callgraph(tmpdir)
        result = backward_slice(graph, target)
        return jsonify(result.to_dict())
    finally:
        shutil.rmtree(tmpdir)

@app.route('/api/demo', methods=['GET'])
def demo():
    # Return pre-computed demo result
    import json
    with open('demo_result.json') as f:
        return jsonify(json.load(f))

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})
```

**Additional requirements:**
- Rate limiting: 10 requests per minute per IP
- Timeout: Kill analysis after 30 seconds
- Max file size: Reject input over 500KB total
- CORS: Allow frontend domain

### `api/requirements.txt`
```
flask>=3.0
flask-cors>=4.0
gunicorn>=21.0
```

### `api/Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY api/requirements.txt ./api_requirements.txt
COPY requirements.txt ./requirements.txt
RUN pip install -r api_requirements.txt -r requirements.txt
COPY src/ ./src/
COPY api/ ./
COPY tests/fixtures/demo_repo/ ./demo_repo/
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--timeout", "60"]
```

### `api/render.yaml`
```yaml
services:
  - type: web
    name: pyanalyze-api
    runtime: docker
    plan: free
    healthCheckPath: /api/health
```

---

## Phase 8: Demo Repo (Day 3 Morning — 1h)

### `tests/fixtures/demo_repo/`

Create a curated example — a small but non-trivial Python project (~5 files, ~15 functions) that produces an interesting, visually appealing call graph. A simplified web scraper:

**`scraper.py`:**
```python
from parser import extract_links, extract_text
from storage import save_result
from config import get_config
from utils import log, retry

def scrape(url):
    config = get_config()
    html = fetch_page(url, config)
    links = extract_links(html)
    text = extract_text(html)
    result = {"url": url, "links": links, "text": text}
    save_result(result)
    log(f"Scraped {url}")
    return result

def fetch_page(url, config):
    timeout = config.get("timeout", 30)
    return retry(lambda: _do_fetch(url, timeout))

def _do_fetch(url, timeout):
    # simulate HTTP request
    return f"<html>content of {url}</html>"
```

**`parser.py`:**
```python
from utils import log, sanitize

def extract_links(html):
    log("Extracting links")
    raw = _find_tags(html, "a")
    return [sanitize(link) for link in raw]

def extract_text(html):
    log("Extracting text")
    raw = _find_tags(html, "p")
    return " ".join(raw)

def _find_tags(html, tag):
    # simplified tag finder
    return [f"content_{tag}_{i}" for i in range(3)]
```

**`storage.py`:**
```python
from utils import log, ensure_dir
from config import get_config

def save_result(data):
    config = get_config()
    path = config.get("output_dir", "./output")
    ensure_dir(path)
    _write_json(path, data)
    log(f"Saved to {path}")

def _write_json(path, data):
    # simulate writing
    pass

def load_results(path):
    log(f"Loading from {path}")
    return []
```

**`config.py`:**
```python
_DEFAULT_CONFIG = {
    "timeout": 30,
    "output_dir": "./output",
    "max_retries": 3,
}

def get_config():
    return _DEFAULT_CONFIG.copy()

def update_config(overrides):
    config = get_config()
    config.update(overrides)
    return config
```

**`utils.py`:**
```python
import os

def log(message):
    print(f"[LOG] {message}")

def sanitize(text):
    return text.strip().lower()

def retry(func, max_attempts=3):
    for i in range(max_attempts):
        try:
            return func()
        except Exception:
            if i == max_attempts - 1:
                raise
    return None

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
```

**Pre-compute the demo result:** After the analysis engine is working, run it on this demo repo and save the JSON output as `web/src/demo/demo_result.json`. The frontend loads this on page load.

---

## Phase 9: React Frontend (Day 3–4 — 10h)

### Tech Stack
- React 18 + Vite
- D3.js v7 (from npm, not CDN)
- Tailwind CSS
- highlight.js (for code syntax highlighting in slice view)

### `web/package.json` dependencies
```json
{
    "dependencies": {
        "react": "^18",
        "react-dom": "^18",
        "d3": "^7",
        "highlight.js": "^11",
        "axios": "^1"
    },
    "devDependencies": {
        "@vitejs/plugin-react": "^4",
        "vite": "^5",
        "tailwindcss": "^3",
        "autoprefixer": "^10",
        "postcss": "^8"
    }
}
```

### App Layout

```
┌──────────────────────────────────────────────────────────────┐
│  PyAnalyze — Python Static Analysis Tool    [GitHub] [Demo]  │
├───────────────────┬──────────────────────────────────────────┤
│                   │                                          │
│   Code Input      │        Call Graph (D3.js)                │
│   (left panel     │        (center, main area)               │
│    ~300px wide)   │                                          │
│                   │        Force-directed layout              │
│   - Paste code    │        Nodes = functions                  │
│   - Upload files  │        Edges = calls (arrows)             │
│   - [Analyze] btn │        Colors = source files              │
│   - [Load Demo]   │        Size = cyclomatic complexity       │
│                   │        Click node → trigger slice          │
│   ─────────────   │        Hover → tooltip with details       │
│                   │        Zoom + pan enabled                  │
│   Function List   │                                          │
│   (clickable,     │                                          │
│    sorted by      │                                          │
│    complexity)    │                                          │
│                   │                                          │
│   ─────────────   ├──────────────────────────────────────────┤
│                   │                                          │
│   Metrics Panel   │   Slice View (appears on node click)     │
│   - Files: 4      │                                          │
│   - Functions: 15 │   ┌─ Dependency Chain ──────────────┐    │
│   - Edges: 22     │   │ utils.log                       │    │
│   - Avg CC: 3.1   │   │   └─ utils.sanitize             │    │
│   - Avg Slice     │   │       └─ parser.extract_links    │    │
│     Reduction:    │   │           └─ scraper.scrape      │    │
│     54%           │   └─────────────────────────────────┘    │
│                   │                                          │
│   Per-function:   │   ┌─ Minimal Code ──────────────────┐    │
│   (when selected) │   │ def log(message):               │    │
│   - LOC: 6        │   │     print(f"[LOG] {message}")   │    │
│   - CC: 2         │   │                                 │    │
│   - Fan-in: 3     │   │ def sanitize(text):             │    │
│   - Fan-out: 2    │   │     return text.strip().lower() │    │
│   - Slice: 55%    │   │                                 │    │
│                   │   │ def extract_links(html):        │    │
│                   │   │     log("Extracting links")     │    │
│                   │   │     ...                         │    │
│                   │   └─────────────────────────────────┘    │
│                   │                                          │
│                   │   Slice: 12 of 27 lines (55% reduction)  │
│                   │                                          │
├───────────────────┴──────────────────────────────────────────┤
│  Built by Xinwei Li | Berkeley CS '27 | GitHub               │
└──────────────────────────────────────────────────────────────┘
```

### Component Details

#### `CallGraph.jsx` — D3.js Visualization (Most Important)

**Requirements:**
- Force-directed graph using `d3.forceSimulation`
- Nodes are circles, radius scaled by cyclomatic complexity: `radius = 8 + complexity * 3` (min 8px, max 30px)
- Nodes colored by source file using `d3.schemeCategory10`
- Edges are lines with arrowhead markers (`marker-end`)
- Node labels show short function name (not qualified — too long)
- Zoom and pan with `d3.zoom()`
- Click a node → call `/api/slice` → highlight slice nodes (dim non-slice nodes to 20% opacity)
- Hover a node → tooltip showing: name, file, LOC, complexity, fan-in, fan-out
- Smooth transitions (500ms) when switching between views
- Double-click background to reset view

**D3 force simulation config:**
```javascript
const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(edges).id(d => d.id).distance(100))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(d => d.radius + 8));
```

**Use a `<svg>` element for the graph, not canvas.** SVG is easier to style, animate, and make interactive.

#### `CodeInput.jsx` — Input Panel

Two input modes:

1. **Paste mode:** `<textarea>` with filename input field above it
   - "Add another file" button adds more textarea+filename pairs
   - Each file entry has a remove button
2. **Upload mode:** Drag-and-drop zone that accepts `.py` files
   - Read files client-side with `FileReader` API
   - Show list of uploaded files with names and sizes

Both modes feed into the same `files[]` array state.

Include a prominent **"Load Demo"** button that fills the input with the demo repo files and auto-triggers analysis.

#### `SliceView.jsx` — Backward Slice Display

Appears when a function node is clicked. Shows:

1. **Dependency chain** as an indented tree (not a graph — simpler to read)
2. **Minimal code** with syntax highlighting via `highlight.js`
3. **Reduction stat** in large text: "12 of 27 lines needed (55% reduction)"

Use `highlight.js` Python language pack for syntax coloring. Import from npm.

#### `MetricsPanel.jsx` — Stats Sidebar

Two sections:

1. **Repository summary** (always visible):
   - Files analyzed, total functions, total edges
   - Average cyclomatic complexity
   - Average slice reduction ratio

2. **Selected function** (visible when a node is clicked):
   - Full qualified name
   - File and line number
   - Lines of code
   - Cyclomatic complexity
   - Fan-in (how many functions call this)
   - Fan-out (how many functions this calls)
   - Slice reduction ratio

#### `useAnalysis.js` — API Hook

```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useAnalysis() {
    const [graph, setGraph] = useState(null);
    const [slice, setSlice] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [files, setFiles] = useState([]);  // current file set

    const analyze = async (files) => {
        setLoading(true);
        setError(null);
        setFiles(files);
        try {
            const res = await axios.post(`${API_URL}/api/analyze`, { files });
            setGraph(res.data);
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    const computeSlice = async (target) => {
        setLoading(true);
        try {
            const res = await axios.post(`${API_URL}/api/slice`, {
                files,
                target
            });
            setSlice(res.data);
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    const loadDemo = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`${API_URL}/api/demo`);
            setGraph(res.data);
        } catch (e) {
            // Fallback: load bundled demo data
            const demoData = await import('./demo/demo_result.json');
            setGraph(demoData.default);
        } finally {
            setLoading(false);
        }
    };

    return { graph, slice, loading, error, analyze, computeSlice, loadDemo };
}
```

### Critical UX Detail: Pre-loaded Demo on Page Load

In `App.jsx`, call `loadDemo()` on mount:
```javascript
useEffect(() => {
    loadDemo();
}, []);
```

Visitors see a fully rendered, interactive call graph the moment the page loads. No blank page, no "paste code to get started." The demo data is bundled in the frontend as fallback in case the API is cold-starting.

---

## Phase 10: Testing (Throughout — woven into each phase)

### Test strategy:

1. **Unit tests** for each module (parser, imports, callgraph, slicer, metrics)
2. **Integration tests** using the fixture repos
3. **API tests** for Flask endpoints

Key test cases:
- Single file with simple call chain
- Cross-file imports (absolute and relative)
- Class methods calling other methods
- Recursive functions (don't infinite loop)
- Circular dependencies between functions
- Empty functions, functions with only docstrings
- Files with syntax errors (skip gracefully, don't crash)
- Functions calling stdlib/third-party (mark as external, don't crash)

Run with: `pytest tests/ -v --cov=src --cov-report=term-missing`

Target: 85%+ code coverage.

---

## Phase 11: Benchmarking (Day 5 — 2h)

### `benchmarks/repos.json`
```json
[
    {"name": "httpx", "url": "https://github.com/encode/httpx"},
    {"name": "rich", "url": "https://github.com/Textualize/rich"},
    {"name": "fastapi", "url": "https://github.com/tiangolo/fastapi"},
    {"name": "black", "url": "https://github.com/psf/black"},
    {"name": "flask", "url": "https://github.com/pallets/flask"}
]
```

### `benchmarks/run_benchmarks.py`

Script that:
1. Clones each repo (or uses local copy)
2. Runs full analysis
3. Outputs a summary table:

```
| Repo     | Files | Functions | Edges | Avg Slice Reduction | Avg CC |
|----------|-------|-----------|-------|---------------------|--------|
| httpx    | 45    | 312       | 487   | 52%                 | 3.1    |
| rich     | 67    | 589       | 1023  | 61%                 | 4.7    |
| fastapi  | 38    | 245       | 398   | 48%                 | 2.8    |
| black    | 23    | 178       | 312   | 57%                 | 5.2    |
| flask    | 31    | 198       | 267   | 53%                 | 3.4    |
| AVERAGE  | 40.8  | 304.4     | 497.4 | 54.2%               | 3.84   |
```

**After running benchmarks, UPDATE the resume numbers to match reality.**

---

## Phase 12: Deployment (Day 5 — 2h)

### Backend → Render (free tier)
1. Push repo to GitHub
2. Connect to Render, select Docker runtime, point to `api/Dockerfile`
3. Set environment variable: `FLASK_ENV=production`
4. Verify `/api/health` returns 200
5. Note URL: `https://pyanalyze-api.onrender.com`

### Frontend → Vercel
1. Set environment variable: `VITE_API_URL=https://pyanalyze-api.onrender.com`
2. Connect GitHub repo to Vercel
3. Root directory: `web/`
4. Build command: `npm run build`
5. Output directory: `dist`
6. Custom domain (optional): `pyanalyze.xinweili.com`

### Render Cold Start Handling
Render free tier sleeps after 15 min of inactivity. First request takes ~30 seconds. Handle this:

1. Frontend bundles `demo_result.json` — demo loads instantly even if API is asleep
2. Show "Connecting to analysis server..." spinner when API call is pending
3. Optional: Use UptimeRobot (free) to ping `/api/health` every 14 minutes to keep it warm

---

## Phase 13: Polish (Day 5 — 2h)

### README.md

```markdown
# PyAnalyze

A static analysis tool for Python that extracts call graphs,
computes backward slices, and visualizes dependencies.

🔗 **[Live Demo](https://pyanalyze.xinweili.com)**

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
pip install -r requirements.txt
pyanalyze analyze /path/to/repo --output graph.json
pyanalyze slice /path/to/repo --target "main.process"

### API
cd api && flask run

### Web
cd web && npm install && npm run dev

## Benchmarks
[Include benchmark table from real results]

## Screenshots
[Include screenshot of the D3 visualization]
```

### `public/index.html` meta tags

```html
<title>PyAnalyze — Python Static Analysis & Dependency Visualization</title>
<meta name="description" content="Interactive tool for Python call graph extraction, backward slicing, and dependency visualization. Built by Xinwei Li at UC Berkeley.">
<meta property="og:title" content="PyAnalyze">
<meta property="og:description" content="Visualize Python dependencies and code complexity">
<meta property="og:image" content="screenshot.png">
```

---

## Dependencies Summary

### Core analysis (`requirements.txt`)
```
networkx>=3.0
click>=8.0
rich>=13.0
pytest>=7.0
pytest-cov>=4.0
```

### API (`api/requirements.txt`)
```
flask>=3.0
flask-cors>=4.0
gunicorn>=21.0
```

### Frontend (`web/package.json`)
```
react, react-dom, d3, highlight.js, axios
vite, tailwindcss, @vitejs/plugin-react
```

No heavy dependencies. No ML libraries. No GPU. Everything runs instantly.

---

## Timeline

| Day | Phase | What | Hours |
|-----|-------|------|-------|
| 1 AM | 1 | AST parsing + data structures | 3h |
| 1 PM | 2 | Import resolution | 3h |
| 1 EVE | 3 | Call graph construction + tests | 3h |
| 2 AM | 4 | Backward slicing ⭐ | 3h |
| 2 PM | 5+6 | Metrics + Export + CLI | 4h |
| 3 AM | 7 | Flask API backend | 3h |
| 3 AM | 8 | Demo repo + pre-compute results | 1h |
| 3 PM | 9 | React: layout + code input + API integration | 4h |
| 4 AM | 9 | React: D3.js call graph visualization | 4h |
| 4 PM | 9 | React: slice view + metrics panel | 2h |
| 5 AM | 10+11 | Tests + benchmarks on real repos | 3h |
| 5 PM | 12+13 | Deploy + polish + README | 3h |

**Total: ~36 hours across 5 days**

---

## Resume Alignment Check

After building, verify every resume claim is backed by real output:

| Resume Claim | Backed By |
|-------------|-----------|
| "parses source code into ASTs" | `src/parser.py` |
| "extracts function-level call graphs" | JSON output nodes + edges |
| "module dependency structures across multi-file repositories" | Cross-file edges in output |
| "backward slicing algorithm" | `src/slicer.py` with correct output |
| "reducing average context size by 55%" | Benchmark results (**adjust to match**) |
| "D3.js rendering call graphs and cyclomatic complexity heatmaps" | Live web demo |
| "Docker for consistent cross-platform execution" | `api/Dockerfile` |
| "batch analysis across 40+ open-source Python repositories" | Expand `repos.json` |
| "pytest-based regression suite" | `pytest tests/` passes |
| "92% precision on dependency edge detection" | Spot-check results (**adjust to match**) |

**CRITICAL: After running benchmarks, replace all fabricated resume numbers with real ones. Real numbers are infinitely better than fake numbers that collapse under scrutiny.**

---

## Definition of Done

The project is "ready to show" when:

1. ✅ Live web demo loads with pre-rendered demo graph instantly
2. ✅ User can paste Python code, click Analyze, see interactive call graph
3. ✅ Clicking any function node shows its backward slice with minimal code
4. ✅ Metrics panel shows real complexity and slice reduction stats
5. ✅ CLI works: `pyanalyze analyze /path/to/repo`
6. ✅ API works: `POST /api/analyze` returns correct JSON
7. ✅ Benchmarks run on 5+ real-world repos with real numbers
8. ✅ Resume numbers match actual benchmark results
9. ✅ Tests pass with 85%+ coverage
10. ✅ Deployed and accessible on personal website URL
11. ✅ GitHub repo has clean README with screenshots
