import os
import shutil
import requests

# Original Stream 
source_urls = {
    "showtv": "https://www.showtv.com.tr/canli-yayin",
    "nowtv": "https://www.nowtv.com.tr/canli-yayin",
    "tv4": "https://www.tv4.com.tr/canli-yayin",
    "kanal7": "https://www.kanal7.com/canli-izle",
    "showturk": "https://www.showturk.com.tr/canli-yayin/showturk",
    "marneulitv": "http://158.101.222.193:88/georgia_play.php?id=marneulitv",
    "vostoktv": "https://limehd.tv/channel/tmb",
    "atvavrupa": "https://www.atvavrupa.tv/canli-yayin",
    "beyaztv": "https://beyaztv.com.tr/canli-yayin",
    # add channels 
}

stream_folder = "stream"

# Əgər stream qovluğu varsa, tam sil
if os.path.exists(stream_folder):
    shutil.rmtree(stream_folder)

# Yenidən stream qovluğunu yarat
os.makedirs(stream_folder)

def extract_m3u8(url):
    """
    yt-dlp istifadə etmədən, birbaşa URL-dən m3u8 linkini çıxarmaq üçün requests istifadə edirik.
    Amma daha mürəkkəb saytlar üçün yt-dlp tövsiyə olunur.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        text = response.text
        
        # Sadə regex və ya axtarışla .m3u8 linki tapılır
        import re
        m3u8_matches = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', text)
        if m3u8_matches:
            return m3u8_matches[0]
        else:
            print(f"{url} saytında m3u8 tapılmadı.")
            return None
    except Exception as e:
        print(f"Xəta: {e}")
        return None

def write_multi_variant_m3u8(filename, url):
    """
    multi-variant m3u8 üçün minimal nümunə yaratmaq:
    """
    content = (
        "#EXTM3U\n"
        "#EXT-X-VERSION:3\n"
        f"#EXT-X-STREAM-INF:BANDWIDTH=1500000,RESOLUTION=1280x720\n"
        f"{url}\n"
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    for name, page_url in source_urls.items():
        m3u8_link = extract_m3u8(page_url)
        if m3u8_link:
            file_path = os.path.join(stream_folder, f"{name}.m3u8")
            write_multi_variant_m3u8(file_path, m3u8_link)
            print(f"{file_path} faylı yaradıldı.")
        else:
            print(f"{name} üçün link tapılmadı.")
