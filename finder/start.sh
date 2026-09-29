#!/bin/zsh
# Start the zero-to-1k finder on http://127.0.0.1:5191 (local only). Nothing is fetched until you press Fetch.
cd "$(dirname "$0")"
command -v treg >/dev/null || { echo "treg is not installed. See AGENTS.md step 1."; exit 1; }
[ -f config.local.json ] || { echo "No config.local.json yet. See AGENTS.md step 2."; exit 1; }
lsof -ti tcp:5191 | xargs kill 2>/dev/null; sleep 1
mkdir -p data; nohup python3 app/finder.py > data/finder.log 2>&1 & echo $! > data/finder.pid
sleep 2; echo "zero-to-1k running: http://127.0.0.1:5191"; open http://127.0.0.1:5191 2>/dev/null || true
