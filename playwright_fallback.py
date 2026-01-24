from typing import List
from playwright.sync_api import sync_playwright


def sniff_m3u8(page_url: str, timeout_ms: int = 60000) -> List[str]:
    found = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def on_request(req):
            url = req.url
            if ".m3u8" in url.lower():
                found.append(url)

        page.on("request", on_request)
        page.goto(page_url, wait_until="networkidle", timeout=timeout_ms)

        browser.close()

    # unique, order preserved
    uniq = []
    seen = set()
    for u in found:
        if u not in seen:
            uniq.append(u)
            seen.add(u)
    return uniq


def choose_best(candidates: List[str]) -> str | None:
    if not candidates:
        return None
    preferred = [c for c in candidates if "master" in c.lower() or "playlist" in c.lower()]
    return preferred[0] if preferred else candidates[0]
