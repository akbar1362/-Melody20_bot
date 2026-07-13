#!/bin/bash

echo "Starting Cloudflare WARP..."
warp-cli registration new 2>/dev/null || true
warp-cli mode proxy 2>/dev/null || true
warp-cli proxy port 40000 2>/dev/null || true
warp-cli connect 2>/dev/null || true

echo "Waiting for WARP to connect..."
sleep 5

echo "Testing proxy..."
curl -s --proxy socks5://127.0.0.1:40000 https://ifconfig.me || echo "Proxy test failed, continuing anyway"

echo "Starting bot..."
python3 bot.py
