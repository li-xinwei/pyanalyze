"""Cross-file import resolution for Python repositories."""

import ast
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class ImportMap:
    """Maps (filepath, local_name) -> (source_filepath, original_name)."""
    symbol_map: Dict[Tuple[str, str], Tuple[str, str]] = field(default_factory=dict)
    module_map: Dict[str, str] = field(default_factory=dict)

    def resolve(self, filepath: str, name: str) -> Optional[Tuple[str, str]]:
        """Resolve a name used in filepath to (source_file, original_name)."""
        return self.symbol_map.get((filepath, name))


def _find_py_files(repo_root: str) -> List[str]:
    """Find all .py files in repository."""
    py_files = []
    for dirpath, _, filenames in os.walk(repo_root):
        for f in filenames:
            if f.endswith(".py"):
                py_files.append(os.path.join(dirpath, f))
    return py_files


def _module_to_filepath(module_name: str, repo_root: str) -> Optional[str]:
    """Convert a dotted module name to a filepath relative to repo_root."""
    parts = module_name.split(".")
    candidates = [
        os.path.join(repo_root, *parts) + ".py",
        os.path.join(repo_root, *parts, "__init__.py"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return os.path.relpath(c, repo_root)
    return None


def _filepath_to_module(filepath: str) -> str:
    """Convert a relative filepath to a module name."""
    mod = filepath.replace(os.sep, ".").replace("/", ".")
    if mod.endswith(".py"):
        mod = mod[:-3]
    if mod.endswith(".__init__"):
        mod = mod[:-9]
    return mod


def _extract_imports(source: str) -> List[dict]:
    """Extract import statements from source code."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    "type": "import",
                    "module": alias.name,
                    "name": alias.name,
                    "alias": alias.asname or alias.name,
                    "level": 0,
                })
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            level = node.level or 0
            for alias in (node.names or []):
                imports.append({
                    "type": "from",
                    "module": module,
                    "name": alias.name,
                    "alias": alias.asname or alias.name,
                    "level": level,
                })
    return imports


def _resolve_relative_import(importing_file: str, module: str,
                             level: int, repo_root: str) -> Optional[str]:
    """Resolve a relative import to an absolute module path."""
    if level == 0:
        return module

    importing_dir = os.path.dirname(importing_file)
    rel_from_root = os.path.relpath(
        os.path.join(repo_root, importing_dir), repo_root
    )
    parts = rel_from_root.split(os.sep)
    if parts == ["."]:
        parts = []

    go_up = level - 1
    if go_up > len(parts):
        return None
    base_parts = parts[:len(parts) - go_up] if go_up > 0 else parts

    if module:
        base_parts.append(module)

    return ".".join(base_parts) if base_parts else module


def build_import_map(repo_root: str) -> ImportMap:
    """Build a complete import map for all Python files in a repository."""
    import_map = ImportMap()
    py_files = _find_py_files(repo_root)

    file_modules = {}
    for fp in py_files:
        rel = os.path.relpath(fp, repo_root)
        mod = _filepath_to_module(rel)
        file_modules[rel] = mod
        import_map.module_map[mod] = rel

    for fp in py_files:
        rel = os.path.relpath(fp, repo_root)
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
        except (IOError, OSError):
            continue

        imports = _extract_imports(source)
        for imp in imports:
            if imp["level"] > 0:
                resolved_module = _resolve_relative_import(
                    rel, imp["module"], imp["level"], repo_root
                )
            else:
                resolved_module = imp["module"]

            if resolved_module is None:
                continue

            if imp["type"] == "from":
                source_file = _module_to_filepath(resolved_module, repo_root)
                if source_file:
                    import_map.symbol_map[(rel, imp["alias"])] = (
                        source_file, imp["name"]
                    )
                else:
                    parent_parts = resolved_module.rsplit(".", 1)
                    if len(parent_parts) == 2:
                        parent_mod, child = parent_parts
                        combined = f"{resolved_module}.{imp['name']}"
                        source_file = _module_to_filepath(combined, repo_root)
                        if source_file:
                            import_map.symbol_map[(rel, imp["alias"])] = (
                                source_file, imp["name"]
                            )
            elif imp["type"] == "import":
                source_file = _module_to_filepath(resolved_module, repo_root)
                if source_file:
                    import_map.symbol_map[(rel, imp["alias"])] = (
                        source_file, resolved_module
                    )

    return import_map
