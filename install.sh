#!/usr/bin/env bash
set -Eeuo pipefail

# Idempotent first-install helper for Ubuntu 24.04 hosts.
REPO_DIR="${MBAS_INSTALL_DIR:-$PWD}"
cd "$REPO_DIR"

command -v docker >/dev/null || { echo "Docker Engine is required." >&2; exit 1; }
docker compose version >/dev/null || { echo "Docker Compose plugin is required." >&2; exit 1; }

if [[ ! -f .env ]]; then
  install -m 600 .env.example .env
  db_password="$(openssl rand -hex 32)"
  auth_secret="$(openssl rand -hex 48)"
  sed -i "s#^POSTGRES_PASSWORD=.*#POSTGRES_PASSWORD=$db_password#; s#^DATABASE_URL=.*#DATABASE_URL=postgresql://mbas:$db_password@postgres:5432/mbas#; s#^AUTH_SECRET=.*#AUTH_SECRET=$auth_secret#" .env
  echo "Created .env with generated database and auth secrets. Set domains/provider credentials before public use."
fi

grep -q '^POSTGRES_PASSWORD=.' .env || { echo "POSTGRES_PASSWORD is required in .env" >&2; exit 1; }
grep -q '^AUTH_SECRET=.' .env || { echo "AUTH_SECRET is required in .env" >&2; exit 1; }
if grep -q 'local-development-only\|replace-with-a-long-random-secret' .env; then
  echo "Replace development placeholder secrets in .env before deployment." >&2
  exit 1
fi

docker compose pull
docker compose up -d --build --remove-orphans
for attempt in {1..30}; do
  if curl -fsS http://127.0.0.1:8000/healthz >/dev/null 2>&1; then break; fi
  sleep 2
done
curl -fsS http://127.0.0.1:8000/readyz >/dev/null
docker compose ps
echo "MBAs is running. Configure DNS for MBAS_DOMAIN and MBAS_API_DOMAIN, then verify HTTPS."
