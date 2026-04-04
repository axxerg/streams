import json
import re
import unicodedata
from pathlib import Path

import requests


API_URL = "https://api.catcast.tv/api/channels"
OUTPUT_FILE = "catcast-config.json"


# Optional: schöne Namen manuell korrigieren
SLUG_OVERRIDES = {
    "KANAL65-HMUSIQI": "kanal-65-hmusiqi",
    "KANAL F": "kanal-f",
    "NOW MUSIC": "now-music",
}


def slugify(text: str) -> str:
    text = text.strip().lower()

    # Sonderzeichen normalisieren (ä → a, etc.)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # alles außer a-z, 0-9 → "-"
    text = re.sub(r"[^a-z0-9]+", "-", text)

    # doppelte "-" entfernen
    text = re.sub(r"-{2,}", "-", text).strip("-")

    return text


def fetch_channels():
    print("📡 Lade Channels von API...")
    response = requests.get(API_URL, timeout=60)
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise ValueError("API response ist kein Array")

    print(f"Gefunden: {len(data)} Channels")
    return data


def build_config(channels):
    result = []
    seen_ids = set()

    for channel in channels:
        channel_id = channel.get("id")
        name = channel.get("name")

        if not channel_id or not name:
            continue

        if channel_id in seen_ids:
            continue
        seen_ids.add(channel_id)

        slug = SLUG_OVERRIDES.get(name, slugify(name))

        result.append({
            "id": str(channel_id),
            "slug": slug
        })

    # alphabetisch sortieren
    result.sort(key=lambda x: x["slug"])

    return result


def save_json(data):
    Path(OUTPUT_FILE).write_text(
        json.dumps(data, ensure_ascii=False, indent=4),
        encoding="utf-8"
    )


def main():
    try:
        channels = fetch_channels()
        config = build_config(channels)

        save_json(config)

        print("\n✅ Fertig!")
        print(f"Datei: {OUTPUT_FILE}")
        print(f"Channels: {len(config)}")

    except Exception as e:
        print(f"❌ Fehler: {e}")


if __name__ == "__main__":
    main()
