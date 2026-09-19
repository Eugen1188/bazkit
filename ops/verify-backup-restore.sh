#!/bin/sh
set -eu

backup_directory="${BACKUP_DIRECTORY:-/backups}"

until pg_isready --quiet; do
  echo "Database is not ready for restore verification yet"
  sleep 2
done

backup_path="$(find "$backup_directory" -maxdepth 1 -type f -name 'bazkit-*.dump' -print | sort | tail -n 1)"
if [ -z "$backup_path" ]; then
  echo "No database backup found in ${backup_directory}" >&2
  exit 1
fi

pg_restore --list "$backup_path" >/dev/null

restore_database="bazkit_restore_check_$(date -u +%Y%m%d%H%M%S)_$$"
case "$restore_database" in
  *[!a-zA-Z0-9_]*)
    echo "Unsafe restore-check database name" >&2
    exit 1
    ;;
esac

cleanup() {
  dropdb --if-exists "$restore_database" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

echo "Restoring ${backup_path} into isolated verification database"
createdb "$restore_database"
pg_restore \
  --exit-on-error \
  --no-owner \
  --no-acl \
  --dbname="$restore_database" \
  "$backup_path"

migration_count="$(psql --dbname="$restore_database" --tuples-only --no-align --command='SELECT COUNT(*) FROM django_migrations;')"
case "$migration_count" in
  ''|*[!0-9]*)
    echo "Restored database did not contain a valid migration history" >&2
    exit 1
    ;;
esac

test "$migration_count" -gt 0
echo "Backup restore verified successfully (${migration_count} migrations)"
