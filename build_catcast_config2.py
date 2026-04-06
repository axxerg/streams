import json
import re
import unicodedata
from pathlib import Path

import requests

BASE_URL = "https://api.catcast.tv/api/channels?page={page}"
OUT_FILE = "catcast-config2.json"
DEBUG_FILE = "catcast-page-debug.json"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text


def score_list(lst):
    if not isinstance(lst, list) or not lst:
        return -1

    dicts = [x for x in lst if isinstance(x, dict)]
    if not dicts:
        return -1

    score = 0
    sample = dicts[:20]
    for item in sample:
        if "id" in item:
            score += 2
        if "name" in item:
            score += 2
        if "shortname" in item:
            score += 1
    return score


def find_best_channel_list(obj, path="root", candidates=None):
    if candidates is None:
        candidates = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}"
            if isinstance(v, list):
                s = score_list(v)
                if s > 0:
                    candidates.append((p, v, s))
            find_best_channel_list(v, p, candidates)

    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            find_best_channel_list(v, f"{path}[{i}]", candidates)

    return candidates


def extract_channel_list(payload):
    candidates = find_best_channel_list(payload)
    if not candidates:
        return None, []

    candidates.sort(key=lambda x: (x[2], len(x[1])), reverse=True)
    best_path, best_list, _ = candidates[0]
    return best_path, best_list


def main():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    items = []
    seen_ids = set()

    for page in range(1, 100):
        url = BASE_URL.format(page=page)
        print(f"Loading page {page}: {url}", flush=True)

        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except Exception as e:
            print(f"Error on page {page}: {e}", flush=True)
            break

        if page == 1:
            Path(DEBUG_FILE).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"Saved debug payload to {DEBUG_FILE}", flush=True)

        best_path, channel_list = extract_channel_list(payload)

        if not channel_list:
            print(f"No more channels on page {page}", flush=True)
            break

        print(f"Using list at {best_path} with {len(channel_list)} entries", flush=True)

        added_this_page = 0

        for ch in channel_list:
            if not isinstance(ch, dict):
                continue

            channel_id = ch.get("id")
            name = ch.get("shortname") or ch.get("name")

            if channel_id is None or not name:
                continue

            channel_id = str(channel_id).strip()
            if not channel_id.isdigit():
                continue

            if channel_id in seen_ids:
                continue
            seen_ids.add(channel_id)

            slug = slugify(str(name))
            if not slug:
                continue

            items.append({
                "id": channel_id,
                "slug": slug
            })
            added_this_page += 1

        print(f"Added {added_this_page} channels from page {page}", flush=True)
        print(f"Total channels so far: {len(items)}", flush=True)

    items.sort(key=lambda x: x["slug"])

    Path(OUT_FILE).write_text(
        json.dumps(items, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8"
    )

    print(f"\nSaved {len(items)} channels to {OUT_FILE}", flush=True)


if __name__ == "__main__":
    main()
