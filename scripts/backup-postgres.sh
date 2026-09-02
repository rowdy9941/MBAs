#!/usr/bin/env bash
set -Eeuo pipefail

if [[ -z "${BACKUP_DIR:-}" || -z "${BACKUP_ENCRYPTION_PASSWORD:-}" ]]; then
  echo "Set BACKUP_DIR and BACKUP_ENCRYPTION_PASSWORD before running backups." >&2
  exit 1
fi
mkdir -p "$BACKUP_DIR"
umask 077
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="$BACKUP_DIR/mbas-$stamp.sql.gz.enc"
docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-mbas}" "${POSTGRES_DB:-mbas}" \
  | gzip | openssl enc -aes-256-cbc -pbkdf2 -salt -pass env:BACKUP_ENCRYPTION_PASSWORD -out "$target"
find "$BACKUP_DIR" -type f -name 'mbas-*.sql.gz.enc' -mtime +30 -delete
echo "Encrypted backup created: $target"
