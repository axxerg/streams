from typing import List
from playwright.sync_api import sync_playwright


def sniff_m3u8(page_url: str, timeout_ms: int = 90000) -> List[str]:
    found: List[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        )
        page = context.new_page()

        def on_request(req):
            url = req.url
            if ".m3u8" in url.lower():
                found.append(url)

        page.on("request", on_request)

        # WICHTIG: nicht networkidle (hängt oft bei Player/Ads)
        page.goto(page_url, wait_until="domcontentloaded", timeout=timeout_ms)

        # etwas Zeit geben, damit Player/XHR die m3u8 anfragt
        page.wait_for_timeout(8000)

        context.close()
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
    preferred = [c for c in candidates if ("master" in c.lower() or "playlist" in c.lower())]
    return preferred[0] if preferred else candidates[0]
