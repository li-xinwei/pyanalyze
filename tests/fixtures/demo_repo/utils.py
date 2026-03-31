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
