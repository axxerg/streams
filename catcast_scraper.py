import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

BASE_URL = "https://catcast.tv"
PAGE_TEMPLATE = "https://catcast.tv/tv/online/?page={page}"
OUTPUT_FILE = "catcast-config.json"
DEBUG_FILE = "catcast-pages-debug.json"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text


def title_from_slug(slug: str) -> str:
    return slug.replace("-", " ").strip()


def extract_channel_links(html: str) -> list[str]:
    patterns = [
        r'href=["\'](/tv/[^"\']+)["\']',
        r'href=["\'](/channel/[^"\']+)["\']',
        r'href=["\'](/live/[^"\']+)["\']',
    ]

    links = []
    for pattern in patterns:
        links.extend(re.findall(pattern, html, flags=re.IGNORECASE))

    clean = []
    seen = set()

    for link in links:
        full = urljoin(BASE_URL, link)

        # nur sinnvolle Channel-Links behalten
        path = urlparse(full).path.lower()
        if "/tv/online" in path:
            continue
        if path.rstrip("/") in ["/tv", "/tv/online", "/"]:
            continue

        if full not in seen:
            seen.add(full)
            clean.append(full)

    return clean


def extract_slug_from_url(url: str) -> str | None:
    path = urlparse(url).path.strip("/")
    parts = [p for p in path.split("/") if p]

    if not parts:
        return None

    # meistens letzter Teil der URL
    slug = parts[-1].strip().lower()

    # offensichtliche Nicht-Slugs raus
    if slug in {"tv", "online", "page"}:
        return None

    slug = slugify(slug)
    return slug or None


def try_extract_id(html: str) -> str | None:
    patterns = [
        r'"id"\s*:\s*(\d{4,})',
        r"channel_id\s*[:=]\s*['\"]?(\d{4,})",
        r"channelId\s*[:=]\s*['\"]?(\d{4,})",
        r'/api/channels/(\d{4,})/',
    ]

    for pattern in patterns:
        m = re.search(pattern, html, flags=re.IGNORECASE)
        if m:
            return m.group(1)

    return None


def load_existing() -> list:
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


def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0"
    })

    debug = {
        "pages": {},
        "channels_found": []
    }

    found = {}
    page_links = {}

    print("Scanne Seiten 1 bis 29...", flush=True)

    for page in range(1, 30):
        url = PAGE_TEMPLATE.format(page=page)
        print(f"Seite {page}: {url}", flush=True)

        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            debug["pages"][str(page)] = {"error": str(e)}
            continue

        links = extract_channel_links(html)
        page_links[page] = links
        debug["pages"][str(page)] = {
            "url": url,
            "links_found": len(links),
            "sample_links": links[:20],
        }

        for link in links:
            slug = extract_slug_from_url(link)
            if not slug:
                continue

            if slug not in found:
                found[slug] = {
                    "id": None,
                    "slug": slug,
                    "source_url": link,
                }

    print(f"Gefundene Slugs aus Seiten: {len(found)}", flush=True)

    print("Lese einzelne Channel-Seiten für IDs...", flush=True)

    for slug, item in found.items():
        url = item["source_url"]
        print(f"- {slug}", flush=True)

        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            html = resp.text
            channel_id = try_extract_id(html)
        except Exception:
            channel_id = None

        item["id"] = channel_id
        debug["channels_found"].append(item.copy())

    result = []
    seen_ids = set()

    existing = load_existing()
    existing_map = {
        str(x.get("id")): x
        for x in existing
        if isinstance(x, dict) and x.get("id")
    }

    for item in found.values():
        cid = item["id"]
        slug = item["slug"]

        if not cid:
            continue
        if cid in seen_ids:
            continue

        seen_ids.add(cid)

        # bestehenden slug behalten, falls vorhanden
        if cid in existing_map and existing_map[cid].get("slug"):
            slug = existing_map[cid]["slug"]

        result.append({
            "id": str(cid),
            "slug": slug
        })

    # alte Einträge ohne Treffer behalten
    existing_ids = {str(x["id"]) for x in result}
    for item in existing:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("id", "")).strip()
        slug = str(item.get("slug", "")).strip()
        if cid and cid not in existing_ids:
            result.append({"id": cid, "slug": slug})

    result.sort(key=lambda x: x["slug"])

    Path(OUTPUT_FILE).write_text(
        json.dumps(result, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8"
    )

    Path(DEBUG_FILE).write_text(
        json.dumps(debug, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8"
    )

    print(f"Gespeichert: {OUTPUT_FILE} ({len(result)} Einträge)", flush=True)
    print(f"Gespeichert: {DEBUG_FILE}", flush=True)


if __name__ == "__main__":
    main()
