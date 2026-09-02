#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ! -f .env ]]; then
  echo "Create .env from .env.example and set production secrets before deployment." >&2
  exit 1
fi

docker compose pull
docker compose up -d --build --remove-orphans
docker compose ps
docker compose exec -T api python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz').read()"

