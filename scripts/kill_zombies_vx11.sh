#!/usr/bin/env bash
# Manual helper to inspect and clean VX11-related zombie processes and containers.
set -euo pipefail

echo "=== VX11 Process Survey (uvicorn/python/docker) ==="
ps -ef | grep -E "(uvicorn|vx11|madre|switch|hormiguero|manifestator|hermes)" | grep -v grep || true

echo
echo "=== Docker containers (all) ==="
docker ps -a || true

read -r -p "Kill uvicorn/hermes/switch processes? [y/N] " kill_uvicorn
if [[ "${kill_uvicorn:-N}" =~ ^[Yy]$ ]]; then
  pkill -9 -f "uvicorn" || true
  pkill -9 -f "madre/main.py" || true
  pkill -9 -f "hormiguero/main.py" || true
  pkill -9 -f "switch/main.py" || true
fi

read -r -p "Prune stopped containers? (docker container prune -f) [y/N] " prune_containers
if [[ "${prune_containers:-N}" =~ ^[Yy]$ ]]; then
  docker container prune -f
fi

read -r -p "Prune dangling images? (docker image prune -f) [y/N] " prune_images
if [[ "${prune_images:-N}" =~ ^[Yy]$ ]]; then
  docker image prune -f
fi

read -r -p "Prune dangling volumes? (docker volume prune -f) [y/N] " prune_volumes
if [[ "${prune_volumes:-N}" =~ ^[Yy]$ ]]; then
  docker volume prune -f
fi

echo "Done. Review output above before rerunning services."
