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


def is_channel_list(value):
    if not isinstance(value, list) or not value:
        return False

    dict_items = [x for x in value if isinstance(x, dict)]
    if not dict_items:
        return False

    score = 0
    sample = dict_items[:10]
    for item in sample:
        if "id" in item:
            score += 1
        if "name" in item:
            score += 1
        if "shortname" in item:
            score += 1

    return score >= len(sample) * 2


def find_best_channel_list(obj, path="root", candidates=None):
    if candidates is None:
        candidates = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}"
            if is_channel_list(value):
                candidates.append((new_path, value))
            find_best_channel_list(value, new_path, candidates)

    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            find_best_channel_list(value, f"{path}[{i}]", candidates)

    return candidates


def extract_channels(payload):
    candidates = find_best_channel_list(payload)

    if not candidates:
        raise ValueError("No channel list candidate found in payload")

    # größte passende Liste nehmen
    candidates.sort(key=lambda x: len(x[1]), reverse=True)
    best_path, best_list = candidates[0]

    print(f"Using channel list at: {best_path}", flush=True)
    print(f"Candidate count: {len(best_list)}", flush=True)

    channels = []
    seen_ids = set()

    for item in best_list:
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

        if cid in seen_ids:
            continue
        seen_ids.add(cid)

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

        if cid in existing_map and existing_map[cid]:
            slug = existing_map[cid]

        if cid in seen:
            continue
        seen.add(cid)

        merged.append({
            "id": cid,
            "slug": slug
        })

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
