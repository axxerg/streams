#!/bin/bash

PAGE="https://www.nowtv.com.tr/canli-yayin"

echo ">>> Lade NOWTV Seite..."

FINAL=$(curl -s "$PAGE" | grep -o "https://nowtv-live-ad\.ercdn\.net[^']*playlist\.m3u8[^']*" | head -n 1)

echo ""
echo "FINAL STREAM:"
echo "$FINAL"

echo ""
echo ">>> Speichere nowtv.m3u8"

cat <<EOF > nowtv.m3u8
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720
$FINAL
EOF

echo ""
echo ">>> Fertig:"
echo "nowtv.m3u8"
