#!/bin/bash

RAW_URL="https://raw.githubusercontent.com/axxerg/streams/refs/heads/main/stream/nowtv.m3u8"

echo ">>> GitHub Stream wird geladen..."

MASTER=$(curl -s "$RAW_URL" | grep "^http")

echo "MASTER:"
echo "$MASTER"

echo ""
echo "FINAL PLAYLIST wird gespeichert..."

curl -sL \
-H "User-Agent: Mozilla/5.0" \
-H "Referer: https://www.nowtv.com.tr/" \
"$MASTER" > final.m3u8

echo ">>> Datei gespeichert:"
echo "final.m3u8"
