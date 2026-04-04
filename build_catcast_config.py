import json
import re
import unicodedata
from pathlib import Path

import requests

API_URL = "https://api.catcast.tv/api/channels"
OUTPUT_FILE = "catcast-config.json"
DEBUG_FILE = "debug-api.json"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text


def find_channel_list(obj):
    """
    Sucht rekursiv nach einer Liste von Channel-Objekten
    mit Feldern wie 'id' und 'name'.
    """
    if isinstance(obj, list):
        if obj and all(isinstance(x, dict) for x in obj):
            sample = obj[0]
            if "id" in sample and "name" in sample:
                return obj

        for item in obj:
            result = find_channel_list(item)
            if result is not None:
                return result

    elif isinstance(obj, dict):
        for value in obj.values():
            result = find_channel_list(value)
            if result is not None:
                return result

    return None


def fetch_channels():
    print("📡 Lade Channels von API...")
    res = requests.get(API_URL, timeout=60)
    res.raise_for_status()

    payload = res.json()

    # Debug immer speichern, damit man die echte Struktur sieht
    Path(DEBUG_FILE).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    channels = find_channel_list(payload)

    if channels is None:
        print("❌ Unbekanntes API-Format")
        if isinstance(payload, dict):
            print("Response keys:", list(payload.keys()))
        else:
            print("Response type:", type(payload).__name__)
        raise ValueError("API liefert keine Channel-Liste")

    print(f"✅ {len(channels)} Channels gefunden")
    return channels


def build_config(channels):
    result = []
    seen_ids = set()

    for ch in channels:
        cid = ch.get("id")
        name = ch.get("name")

        if cid is None or not name:
            continue

        if cid in seen_ids:
            continue
        seen_ids.add(cid)

        result.append({
            "id": str(cid),
            "slug": slugify(name)
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

    print(f"💾 Gespeichert: {OUTPUT_FILE}")
    print(f"📺 Channels: {len(config)}")


if __name__ == "__main__":
    main()
