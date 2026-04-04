import json
import re
import unicodedata
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

API_URL = "https://api.catcast.tv/api/channels"
PAGE_URL = "https://catcast.tv/tv/"
OUTPUT_FILE = "catcast-config.json"
DEBUG_FILE = "catcast-debug.json"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text


def add_channel(found: dict, cid, name):
    if cid is None or not name:
        return
    cid = str(cid).strip()
    name = str(name).strip()
    if not cid or not name:
        return
    found[cid] = {
        "id": cid,
        "slug": slugify(name)
    }


def walk_for_channels(obj, found: dict):
    if isinstance(obj, dict):
        if "id" in obj and "name" in obj:
            add_channel(found, obj.get("id"), obj.get("name"))
        for value in obj.values():
            walk_for_channels(value, found)

    elif isinstance(obj, list):
        for item in obj:
            walk_for_channels(item, found)


def walk_for_pagination_urls(obj, urls: set):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and value.startswith("http"):
                key_l = key.lower()
                if "page" in key_l or "next" in key_l or "url" in key_l:
                    urls.add(value)
            else:
                walk_for_pagination_urls(value, urls)

    elif isinstance(obj, list):
        for item in obj:
            walk_for_pagination_urls(item, urls)


def fetch_json(url: str):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.json()


def collect_from_api(found: dict, debug: dict):
    seen_urls = set()
    queue = [API_URL]

    while queue:
        url = queue.pop(0)
        if url in seen_urls:
            continue
        seen_urls.add(url)

        try:
            payload = fetch_json(url)
        except Exception as e:
            debug.setdefault("api_errors", []).append({"url": url, "error": str(e)})
            continue

        debug.setdefault("api_payloads", []).append({"url": url, "type": type(payload).__name__})

        walk_for_channels(payload, found)

        discovered_urls = set()
        walk_for_pagination_urls(payload, discovered_urls)

        for next_url in discovered_urls:
            if "api.catcast.tv" in next_url and next_url not in seen_urls:
                queue.append(next_url)


def collect_from_page(found: dict, debug: dict):
    responses_seen = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def on_response(response):
            url = response.url
            if "api.catcast.tv" not in url:
                return
            try:
                data = response.json()
                responses_seen.append(url)
                walk_for_channels(data, found)
            except Exception:
                pass

        page.on("response", on_response)

        page.goto(PAGE_URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(5000)

        # mehr Inhalt triggern
        for _ in range(8):
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(1500)

        # mögliche Buttons/Tabs anklicken
        selectors = [
            "button",
            "[role='tab']",
            "a",
            ".tab",
            ".tabs button",
            ".tabs a",
            ".category",
            ".categories button",
            ".categories a",
        ]

        clicked = set()
        for selector in selectors:
            try:
                elements = page.locator(selector)
                count = min(elements.count(), 40)
                for i in range(count):
                    try:
                        el = elements.nth(i)
                        text = (el.inner_text(timeout=1000) or "").strip()
                        key = f"{selector}:{text}"
                        if not text or key in clicked:
                            continue
                        clicked.add(key)
                        el.click(timeout=1000)
                        page.wait_for_timeout(1500)
                    except Exception:
                        pass
            except Exception:
                pass

        page.wait_for_timeout(5000)
        browser.close()

    debug["page_api_calls"] = sorted(set(responses_seen))


def load_existing():
    path = Path(OUTPUT_FILE)
    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except Exception:
        pass

    return []


def merge_existing(existing: list, found: dict):
    merged = []
    seen = set()

    # bestehende Reihenfolge behalten
    for item in existing:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("id", "")).strip()
        slug = str(item.get("slug", "")).strip()
        if not cid:
            continue

        if cid in found and not slug:
            slug = found[cid]["slug"]

        merged.append({"id": cid, "slug": slug})
        seen.add(cid)

    # neue Sender anhängen
    new_items = [v for k, v in found.items() if k not in seen]
    new_items.sort(key=lambda x: x["slug"])
    merged.extend(new_items)

    return merged


def main():
    found = {}
    debug = {}

    existing = load_existing()
    print(f"Loaded existing entries: {len(existing)}")

    print("Collecting from API...")
    collect_from_api(found, debug)
    print(f"Found after direct API scan: {len(found)}")

    print("Collecting from page/network...")
    collect_from_page(found, debug)
    print(f"Found after page scan: {len(found)}")

    merged = merge_existing(existing, found)

    Path(OUTPUT_FILE).write_text(
        json.dumps(merged, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8"
    )

    debug["total_found"] = len(found)
    debug["total_merged"] = len(merged)

    Path(DEBUG_FILE).write_text(
        json.dumps(debug, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8"
    )

    print(f"Saved merged config: {OUTPUT_FILE} ({len(merged)} entries)")
    print(f"Saved debug file: {DEBUG_FILE}")


if __name__ == "__main__":
    main()
