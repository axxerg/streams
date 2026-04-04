import json
import re
import unicodedata
from pathlib import Path

import requests

API_URL = "https://api.catcast.tv/api/channels"
OUTPUT_FILE = "catcast-config.json"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text


def fetch_channels():
    print("📡 Lade Channels von API...")
    res = requests.get(API_URL, timeout=60)
    res.raise_for_status()

    data = res.json()

    # 🔥 FIX: verschiedene API-Formate abfangen
    if isinstance(data, list):
        channels = data
    elif isinstance(data, dict):
        channels = (
            data.get("data")
            or data.get("channels")
            or data.get("result")
            or data.get("items")
        )
    else:
        channels = None

    if not isinstance(channels, list):
        print("❌ Unbekanntes API-Format")
        print("Response keys:", list(data.keys()) if isinstance(data, dict) else type(data))

        # Debug speichern
        Path("debug-api.json").write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        raise ValueError("API liefert keine Channel-Liste")

    print(f"✅ {len(channels)} Channels gefunden")
    return channels


def build_config(channels):
    result = []
    seen = set()

    for ch in channels:
        cid = ch.get("id")
        name = ch.get("name")

        if not cid or not name:
            continue

        if cid in seen:
            continue
        seen.add(cid)

        slug = slugify(name)

        result.append({
            "id": str(cid),
            "slug": slug
        })

    result.sort(key=lambda x: x["slug"])
    return result


def main():
    channels = fetch_channels()
    config = build_config(channels)

    Path(OUTPUT_FILE).write_text(
        json.dumps(config, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    print(f"\n💾 Gespeichert: {OUTPUT_FILE}")
    print(f"📺 Channels: {len(config)}")


if __name__ == "__main__":
    main()
