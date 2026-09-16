# Bazkit operations

## Database backups

The `backup` Compose service creates a verified PostgreSQL custom-format dump
when it starts and then once every 24 hours. Backups are kept in the local
`backups/` directory for 14 days by default. When off-site backups and the R2
backup bucket are configured, every verified dump is also uploaded under the
`database-backups/` prefix and checked by file size after the upload.

Create an additional backup manually before a risky operation:

```sh
docker compose run --rm -e BACKUP_ONCE=true backup
```

Validate a backup without changing the database:

```sh
docker compose exec -T backup pg_restore --list /backups/<backup-file>.dump >/dev/null
```

Restoring a backup replaces database data and therefore remains an explicit
operator task. Stop the backend first, keep a second copy of the selected dump,
and validate the dump with `pg_restore --list` before restoring it.

Use a separate private R2 bucket for database backups and set its name as
`R2_BACKUP_BUCKET_NAME`. Never use the public media bucket for database dumps.
After a successful manual test, set `OFFSITE_BACKUP_ENABLED=True` and
`OFFSITE_BACKUP_REQUIRED=True`, so a missing upload configuration also stops a
deployment before migrations.

## Availability monitoring

The `Monitor Bazkit` GitHub Actions workflow checks `/health/` every 15 minutes.
The endpoint verifies both Django and its database connection. A failed check is
visible as a failed workflow run and can use the repository's normal GitHub
Actions notifications. Until a domain is available, the workflow uses the
server address stored in the existing `SERVER_HOST` repository secret.
