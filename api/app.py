"""Flask API wrapping the src/ analysis pipeline."""

import json
import os
import shutil
import sys
import tempfile

from flask import Flask, request, jsonify
from flask_cors import CORS

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.parser import parse_file
from src.callgraph import build_callgraph
from src.slicer import backward_slice
from src.export import to_json

app = Flask(__name__)
CORS(app)

MAX_TOTAL_SIZE = 500 * 1024  # 500KB

DEMO_RESULT_PATH = os.path.join(os.path.dirname(__file__), "demo_result.json")
DEMO_REPO_PATH = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures", "demo_repo")


def _write_files_to_tmpdir(files):
    """Write uploaded files to a temporary directory."""
    tmpdir = tempfile.mkdtemp()
    for f in files:
        filepath = os.path.join(tmpdir, f["name"])
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as fh:
            fh.write(f["content"])
    return tmpdir


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    files = data.get("files", [])
    if not files:
        return jsonify({"error": "No files provided"}), 400

    total_size = sum(len(f.get("content", "")) for f in files)
    if total_size > MAX_TOTAL_SIZE:
        return jsonify({"error": "Total file size exceeds 500KB limit"}), 400

    tmpdir = _write_files_to_tmpdir(files)
    try:
        graph = build_callgraph(tmpdir)
        result = to_json(graph)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@app.route("/api/slice", methods=["POST"])
def slice_endpoint():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    files = data.get("files", [])
    target = data.get("target", "")

    if not target:
        return jsonify({"error": "No target function specified"}), 400

    if not files:
        return jsonify({"error": "No files provided"}), 400

    tmpdir = _write_files_to_tmpdir(files)
    try:
        graph = build_callgraph(tmpdir)
        result = backward_slice(graph, target)
        return jsonify({"slice": result.to_dict()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@app.route("/api/demo", methods=["GET"])
def demo():
    if os.path.exists(DEMO_RESULT_PATH):
        with open(DEMO_RESULT_PATH) as f:
            return jsonify(json.load(f))

    if os.path.isdir(DEMO_REPO_PATH):
        graph = build_callgraph(DEMO_REPO_PATH)
        result = to_json(graph)
        return jsonify(result)

    return jsonify({"error": "Demo data not available"}), 404


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=8000)
