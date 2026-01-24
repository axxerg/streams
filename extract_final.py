import os
import shutil
import requests
import re

from playwright_fallback import sniff_m3u8, choose_best


# Original Stream Pages
source_urls = {
    "showtv": "https://www.showtv.com.tr/canli-yayin",
    "nowtv": "https://www.nowtv.com.tr/canli-yayin",
    "tv4": "https://www.tv4.com.tr/canli-yayin",
    "kanal7": "https://www.kanal7.com/canli-izle",
    "atvavrupa": "https://www.atvavrupa.tv/canli-yayin",
    "beyaztv": "https://beyaztv.com.tr/canli-yayin",
}

# Sender, die JS / Adblock haben → Playwright
PLAYWRIGHT_FALLBACK = {
    "atvavrupa",
}

stream_folder = "stream"

# stream-Ordner neu erstellen
if os.path.exists(stream_folder):
    shutil.rmtree(stream_folder)
os.makedirs(stream_folder, exist_ok=True)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,tr;q=0.8,en;q=0.7",
}


def extract_m3u8(url):
    """
    Versucht per requests eine m3u8 direkt aus dem HTML zu extrahieren.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        text = response.text

        matches = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', text)
        if matches:
            return matches[0]

        print(f"[MISS] Keine m3u8 im HTML gefunden: {url}")
        return None

    except Exception as e:
        print(f"[ERROR] {url} → {e}")
        return None


def write_multi_variant_m3u8(filename, url):
    """
    Erzeugt eine einfache Wrapper-m3u8
    """
    content = (
        "#EXTM3U\n"
        "#EXT-X-VERSION:3\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=1500000,RESOLUTION=1280x720\n"
        f"{url}\n"
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    for name, page_url in source_urls.items():
        print(f"\n=== {name} ===")

        # 1️⃣ Normaler Versuch (requests)
        m3u8_link = extract_m3u8(page_url)

        # 2️⃣ Playwright-Fallback
        if not m3u8_link and name in PLAYWRIGHT_FALLBACK:
            print("[INFO] requests erfolglos → Playwright wird verwendet")
            candidates = sniff_m3u8(page_url)
            m3u8_link = choose_best(candidates)

        # 3️⃣ Ergebnis
        if m3u8_link:
            file_path = os.path.join(stream_folder, f"{name}.m3u8")
            write_multi_variant_m3u8(file_path, m3u8_link)
            print(f"[OK] {file_path} erstellt")
        else:
            print(f"[FAIL] Kein Stream gefunden für {name}")
