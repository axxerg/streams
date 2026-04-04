import json
import re
import unicodedata
import requests

BASE_URL = "https://api.catcast.tv/api/channels?page={page}"
OUT_FILE = "catcast-config.json"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text


items = []
seen = set()

for page in range(1, 30):
    url = BASE_URL.format(page=page)
    print(f"Lade {url}", flush=True)

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        payload = r.json()
    except Exception as e:
        print(f"Fehler auf Seite {page}: {e}", flush=True)
        continue

    data_obj = payload.get("data", {})
    channel_list = data_obj.get("data", [])

    if not isinstance(channel_list, list):
        print(f"Seite {page}: keine Liste unter data.data", flush=True)
        continue

    for ch in channel_list:
        cid = ch.get("id")
        name = ch.get("shortname") or ch.get("name")

        if cid is None or not name:
            continue

        cid = str(cid)
        if cid in seen:
            continue
        seen.add(cid)

        slug = slugify(str(name))

        items.append({
            "id": cid,
            "slug": slug
        })

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(items, f, indent=4, ensure_ascii=False)

print(f"Fertig: {len(items)} Einträge in {OUT_FILE}", flush=True)
