#!/bin/bash
# Quick health verification for the running optimizer
PORT="${1:-5000}"

echo "==> Process:"
pgrep -fl web_app_prod.py || echo "    NOT RUNNING"

echo "==> Port $PORT:"
(curl -s "http://127.0.0.1:$PORT/api/health" && echo) || echo "    no response"

echo "==> Presets:"
(curl -s "http://127.0.0.1:$PORT/api/presets" && echo) || true
