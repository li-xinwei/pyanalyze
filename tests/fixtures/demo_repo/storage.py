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
