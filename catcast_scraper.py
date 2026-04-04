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


def add_channel(found: dict, cid, name):
    if cid is None or name is None:
        return

    cid = str(cid).strip()
    name = str(name).strip()

    if not cid or not name:
        return

    # nur numerische IDs
    if not cid.isdigit():
        return

    # offensichtlichen Müll rausfiltern
    if len(cid) < 5:
        return

    slug = slugify(name)
    if not slug:
        return

    if slug == "name":
        return

    found[cid] = {
        "id": cid,
        "slug": slug
    }


def walk(obj, found: dict):
    if isinstance(obj, dict):
        if "id" in obj and "name" in obj:
            add_channel(found, obj.get("id"), obj.get("name"))
        for value in obj.values():
            walk(value, found)
    elif isinstance(obj, list):
        for item in obj:
            walk(item, found)


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

        if not cid or not cid.isdigit():
            continue
        if len(cid) < 5:
            continue

        if not slug and cid in found:
            slug = found[cid]["slug"]

        if not slug:
            continue

        if cid in seen:
            continue

        merged.append({
            "id": cid,
            "slug": slug
        })
        seen.add(cid)

    new_items = [v for k, v in found.items() if k not in seen]
    new_items.sort(key=lambda x: x["slug"])
    merged.extend(new_items)

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
        json.dumps(payload, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8"
    )
    print(f"Saved raw API response to {DEBUG_FILE}", flush=True)

    found = {}
    walk(payload, found)
    print(f"Valid channels found recursively: {len(found)}", flush=True)

    merged = merge_existing(existing, found)

    Path(OUTPUT_FILE).write_text(
        json.dumps(merged, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8"
    )

    print(f"Saved merged config to {OUTPUT_FILE}", flush=True)
    print(f"Merged entries: {len(merged)}", flush=True)


if __name__ == "__main__":
    main()
