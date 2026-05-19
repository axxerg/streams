#!/bin/bash

RAW_URL="https://raw.githubusercontent.com/axxerg/streams/refs/heads/main/stream/nowtv.m3u8"

echo ">>> Lade RAW Datei..."

curl -s "$RAW_URL"

echo ""
echo ">>> Extrahiere Stream..."

MASTER=$(curl -s "$RAW_URL" | grep "^http")

echo "MASTER=$MASTER"

if [ -z "$MASTER" ]; then
    echo "FEHLER: Kein Stream gefunden!"
    exit 1
fi

echo ""
echo ">>> Speichere final.m3u8"

curl -L \
-H "User-Agent: Mozilla/5.0" \
-H "Referer: https://www.nowtv.com.tr/" \
"$MASTER" -o final.m3u8

echo ""
echo ">>> Prüfe Datei..."

ls -lah final.m3u8

echo ""
cat final.m3u8
