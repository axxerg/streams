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

    new_items = [v for k, v in found.items() if k not in seen]
    new_items.sort(key=lambda x: x["slug"])
    merged.extend(new_items)

    return merged


def main():
    found = {}
    debug = {
        "api_calls": [],
        "errors": [],
    }

    print("Step 1: load existing config", flush=True)
    existing = load_existing()
    print(f"Existing entries: {len(existing)}", flush=True)

    print("Step 2: direct API request", flush=True)
    try:
        r = requests.get(API_URL, timeout=60)
        r.raise_for_status()
        payload = r.json()
        walk_for_channels(payload, found)
        print(f"Found after direct API: {len(found)}", flush=True)
    except Exception as e:
        debug["errors"].append(f"direct api error: {e}")
        print(f"Direct API error: {e}", flush=True)

    print("Step 3: open page with Playwright", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def on_response(response):
            url = response.url
            if "api.catcast.tv" not in url:
                return
            debug["api_calls"].append(url)
            try:
                data = response.json()
                before = len(found)
                walk_for_channels(data, found)
                after = len(found)
                if after != before:
                    print(f"Captured from network: +{after - before} channels -> total {after}", flush=True)
            except Exception as e:
                debug["errors"].append(f"response parse error for {url}: {e}")

        page.on("response", on_response)

        print("Opening page...", flush=True)
        page.goto(PAGE_URL, wait_until="domcontentloaded", timeout=60000)
        print("Page opened", flush=True)

        page.wait_for_timeout(5000)
        print("Waited 5s", flush=True)

        for i in range(3):
            page.mouse.wheel(0, 2500)
            page.wait_for_timeout(1500)
            print(f"Scroll {i+1}/3 done", flush=True)

        browser.close()
        print("Browser closed", flush=True)

    print(f"Found after page/network: {len(found)}", flush=True)

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

    print(f"Saved {OUTPUT_FILE} with {len(merged)} entries", flush=True)
    print(f"Saved {DEBUG_FILE}", flush=True)


if __name__ == "__main__":
    main()
