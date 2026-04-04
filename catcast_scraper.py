import json
import re
import unicodedata
from pathlib import Path

import requests

API_URL = "https://api.catcast.tv/api/channels"
OUTPUT_FILE = "catcast-config.json"
DEBUG_FILE = "catcast-debug.json"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text


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


def extract_channels(payload):
    if not isinstance(payload, dict):
        raise ValueError("API root is not an object")

    data = payload.get("data")
    if not isinstance(data, list):
        raise ValueError("payload['data'] is not a list")

    channels = []
    for item in data:
        if not isinstance(item, dict):
            continue

        cid = item.get("id")
        name = item.get("name")

        if cid is None or not name:
            continue

        cid = str(cid).strip()
        name = str(name).strip()

        if not cid.isdigit():
            continue
        if len(cid) < 5:
            continue

        slug = slugify(name)
        if not slug:
            continue

        channels.append({
            "id": cid,
            "slug": slug
        })

    return channels


def merge_existing(existing, fresh):
    existing_map = {}
    for item in existing:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("id", "")).strip()
        slug = str(item.get("slug", "")).strip()
        if cid:
            existing_map[cid] = slug

    merged = []
    seen = set()

    for item in fresh:
        cid = item["id"]
        slug = item["slug"]

        # vorhandenen slug behalten, falls schon gesetzt
        if cid in existing_map and existing_map[cid]:
            slug = existing_map[cid]

        if cid in seen:
            continue
        seen.add(cid)

        merged.append({
            "id": cid,
            "slug": slug
        })

    # alte Einträge behalten, die nicht mehr in fresh sind
    for cid, slug in existing_map.items():
        if cid not in seen:
            merged.append({
                "id": cid,
                "slug": slug
            })

    return merged


def main():
    print("Loading existing config...", flush=True)
    existing = load_existing()
    print(f"Existing entries: {len(existing)}", flush=True)

    print(f"Requesting: {API_URL}", flush=True)
    response = requests.get(API_URL, timeout=(20, 60))
    print(f"HTTP status: {response.status_code}", flush=True)
    response.raise_for_status()

    payload = response.json()

    Path(DEBUG_FILE).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print(f"Saved raw API response to {DEBUG_FILE}", flush=True)

    fresh = extract_channels(payload)
    print(f"Fresh valid channels: {len(fresh)}", flush=True)

    merged = merge_existing(existing, fresh)

    Path(OUTPUT_FILE).write_text(
        json.dumps(merged, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8"
    )

    print(f"Saved merged config to {OUTPUT_FILE}", flush=True)
    print(f"Merged entries: {len(merged)}", flush=True)


if __name__ == "__main__":
    main()
