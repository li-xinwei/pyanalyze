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
