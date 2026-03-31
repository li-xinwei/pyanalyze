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
