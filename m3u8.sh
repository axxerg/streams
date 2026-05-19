#!/bin/bash

PAGE="https://www.nowtv.com.tr/canli-yayin"

echo ">>> Lade Webseite..."

HTML=$(curl -s "$PAGE")

echo ">>> Suche echten Stream..."

FINAL=$(echo "$HTML" | grep -o "https://nowtv-live-ad\.ercdn\.net[^']*")

echo ""
echo "STREAM:"
echo "$FINAL"

# Prüfen ob leer
if [ -z "$FINAL" ]; then
    echo "FEHLER: Kein Stream gefunden!"
    exit 1
fi

echo ""
echo ">>> Speichere Datei..."

echo "#EXTM3U" > nowtv.m3u8
echo "#EXT-X-VERSION:3" >> nowtv.m3u8
echo "#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720" >> nowtv.m3u8
echo "$FINAL" >> nowtv.m3u8

echo ""
echo ">>> Datei erstellt:"
ls -lah nowtv.m3u8

echo ""
cat nowtv.m3u8
