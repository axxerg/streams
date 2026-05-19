#!/bin/bash

PAGE="https://www.nowtv.com.tr/canli-yayin"

echo ">>> Lade Webseite..."

HTML=$(curl -s "$PAGE")

echo ">>> Suche Stream..."

FINAL=$(echo "$HTML" | grep -o "https://nowtv-live-ad\.ercdn\.net[^']*")

echo "STREAM:"
echo "$FINAL"

if [ -z "$FINAL" ]; then
    echo "FEHLER: Kein Stream gefunden!"
    exit 1
fi

mkdir -p stream

echo "#EXTM3U" > stream/nowtv.m3u8
echo "#EXT-X-VERSION:3" >> stream/nowtv.m3u8
echo "#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720" >> stream/nowtv.m3u8
echo "$FINAL" >> stream/nowtv.m3u8

echo ">>> Datei erstellt"

cat stream/nowtv.m3u8

# GIT PUSH
git config --global user.email "action@github.com"
git config --global user.name "GitHub Action"

git add stream/nowtv.m3u8

git commit -m "Update nowtv stream" || echo "Keine Änderungen"

git push
