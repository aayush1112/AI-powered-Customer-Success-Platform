#!/usr/bin/env bash
# ============================================================
# backup.sh — PostgreSQL database backup
# Usage: ./scripts/backup.sh
# Cron example (daily at 2am):
#   0 2 * * * /opt/csp/scripts/backup.sh >> /var/log/csp-backup.log 2>&1
# ============================================================
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/csp}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/csp-db-$TIMESTAMP.sql.gz"

# Load environment (adjust path if needed)
if [ -f .env ]; then
    set -a; source .env; set +a
fi

POSTGRES_USER="${POSTGRES_USER:-csp_user}"
POSTGRES_DB="${POSTGRES_DB:-csp_db}"

mkdir -p "$BACKUP_DIR"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting backup: $BACKUP_FILE"

docker compose exec -T postgres pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --no-owner \
    --no-acl \
    | gzip > "$BACKUP_FILE"

SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Backup complete: $BACKUP_FILE ($SIZE)"

# Remove backups older than RETENTION_DAYS
find "$BACKUP_DIR" -name "csp-db-*.sql.gz" -mtime "+$RETENTION_DAYS" -delete
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Pruned backups older than $RETENTION_DAYS days"
