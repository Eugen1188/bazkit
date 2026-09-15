#!/bin/sh
set -eu

backup_directory="${BACKUP_DIRECTORY:-/backups}"
backup_interval_seconds="${BACKUP_INTERVAL_SECONDS:-86400}"
backup_retention_days="${BACKUP_RETENTION_DAYS:-14}"

wait_for_database() {
  until pg_isready --quiet; do
    echo "Database is not ready for backup yet"
    sleep 5
  done
}

create_backup() {
  timestamp="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
  target_path="${backup_directory}/bazkit-${timestamp}.dump"
  temporary_path="${target_path}.tmp"

  mkdir -p "$backup_directory"
  rm -f "$temporary_path"

  echo "Creating database backup ${target_path}"
  pg_dump \
    --format=custom \
    --no-owner \
    --no-acl \
    --file="$temporary_path"

  pg_restore --list "$temporary_path" >/dev/null
  mv "$temporary_path" "$target_path"

  find "$backup_directory" \
    -type f \
    -name 'bazkit-*.dump' \
    -mtime "+${backup_retention_days}" \
    -delete

  echo "Database backup completed: ${target_path}"
}

wait_for_database
create_backup

if [ "${BACKUP_ONCE:-false}" = "true" ]; then
  exit 0
fi

while true; do
  sleep "$backup_interval_seconds"
  wait_for_database
  create_backup
done
