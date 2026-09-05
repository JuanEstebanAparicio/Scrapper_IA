# src/scrape_extract.py
import requests
from bs4 import BeautifulSoup
import time
import json
import re
import os
from urllib.parse import urlparse, urljoin
import sys

USER_AGENT = "Mozilla/5.0 (compatible; ScraperBot/1.0; +https://example.com/bot)"
HEADERS = {"User-Agent": USER_AGENT}
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def allowed_by_robots(base_url, path="/"):
    try:
        robots_url = urljoin(base_url, "/robots.txt")
        r = requests.get(robots_url, headers=HEADERS, timeout=6)
        if r.status_code != 200:
            return True
        txt = r.text
        # heurística simple: si Disallow: / aparece, bloquea todo
        for line in txt.splitlines():
            line = line.strip()
            if line.lower().startswith("user-agent:"):
                current = line.split(":",1)[1].strip()
            if line.lower().startswith("disallow:"):
                rule = line.split(":",1)[1].strip()
                if rule == "/":
                    return False
        return True
    except Exception:
        return True

def fetch_html(url, timeout=12):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text

def extract_code_blocks(html, base_url=None):
    soup = BeautifulSoup(html, "html.parser")
    blocks = []
    # buscar <pre> y <code>
    for tag in soup.find_all(["pre", "code"]):
        text = tag.get_text()
        if len(text.strip()) < 8:
            continue
        blocks.append({"source": "pre/code", "code": text.strip(), "context": tag.parent.name})
    # buscar bloques con clases comunes (ej: .highlight, .language-js)
    selectors = ['.highlight', '.code', '.language-python', '.language-javascript', '.example']
    for sel in selectors:
        for tag in soup.select(sel):
            text = tag.get_text()
            if len(text.strip()) < 8:
                continue
            blocks.append({"source": sel, "code": text.strip(), "context": tag.name})
    # heurística: buscar <script> con texto no vacío (no inline src)
    for s in soup.find_all("script"):
        if s.get("src"):
            continue
        text = s.string or ""
        if len(text.strip()) > 20:
            blocks.append({"source": "inline_script", "code": text.strip(), "context": "script"})
    # limpiar y deduplicar
    seen = set()
    cleaned = []
    for b in blocks:
        code = re.sub(r'\r\n', '\n', b["code"]).strip()
        key = code[:200]  # dedupe por prefijo
        if key in seen:
            continue
        seen.add(key)
        cleaned.append({"code": code, "source": b["source"], "context": b["context"]})
    return cleaned

def save_json(payload, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path

def main(url):
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if not allowed_by_robots(base, parsed.path):
        print("Scraping bloqueado por robots.txt. Abortando.")
        return
    print(f"Descargando {url}")
    html = fetch_html(url)
    blocks = extract_code_blocks(html, base_url=base)
    meta = {"url": url, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "count": len(blocks)}
    payload = {"meta": meta, "blocks": blocks}
    filename = re.sub(r'[^a-z0-9]', '_', parsed.path.strip("/")) or "root"
    filename = f"{parsed.netloc}_{filename}.json"
    out = save_json(payload, filename)
    print(f"Guardado {out} con {len(blocks)} bloques.")
    # pausa corta para respetar rate limits
    time.sleep(1.2)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python src/scrape_extract.py <URL>")
        sys.exit(1)
    url = sys.argv[1]
    main(url)
