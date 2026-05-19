#!/bin/bash

URL="https://raw.githubusercontent.com/axxerg/streams/refs/heads/main/stream/nowtv.m3u8"

STREAM=$(curl -s "$URL" | grep "^http")

echo "$STREAM"
