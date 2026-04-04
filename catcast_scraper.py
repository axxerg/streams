import json
import re
import unicodedata
from pathlib import Path

from playwright.sync_api import sync_playwright

PAGE_URL = "https://catcast.tv/tv/"
OUTPUT_FILE = "catcast-config.json"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text


def find_channels(obj, found):
    if isinstance(obj, list):
        for item in obj:
            find_channels(item, found)
    elif isinstance(obj, dict):
        if "id" in obj and "name" in obj:
            cid = obj.get("id")
            name = obj.get("name")
            if cid is not None and name:
                found[str(cid)] = {
                    "id": str(cid),
                    "slug": slugify(str(name))
                }
        for value in obj.values():
            find_channels(value, found)


def main():
    found = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def handle_response(response):
            url = response.url
            if "api.catcast.tv" not in url:
                return
            try:
                data = response.json()
                find_channels(data, found)
            except Exception:
                pass

        page.on("response", handle_response)

        page.goto(PAGE_URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(15000)

        browser.close()

    result = sorted(found.values(), key=lambda x: x["slug"])

    Path(OUTPUT_FILE).write_text(
        json.dumps(result, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8"
    )

    print(f"Saved {len(result)} channels to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
