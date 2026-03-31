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
