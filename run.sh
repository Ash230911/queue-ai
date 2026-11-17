#!/usr/bin/env bash
# One-command start: installs deps, builds the website if Node is present, starts the API on :8000
set -e
[ -d venv ] || python3 -m venv venv
. venv/bin/activate
pip install -q -r requirements.txt
if command -v npm >/dev/null 2>&1; then (cd web && npm install --silent && npm run build --silent); else echo "Node not found: skipping website build (API still works at /docs)"; fi
uvicorn api.main:app --host 0.0.0.0 --port 8000
