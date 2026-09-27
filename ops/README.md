# Bazkit operations

## Deployment secrets

Production deployments expect `OPENAI_API_KEY` as a GitHub Actions repository
secret. The deployment forwards it directly to Docker Compose and verifies that
the running backend received it. The key is never written to the repository or
printed by the deployment script.

Create a dedicated project API key for Bazkit and store it in GitHub under
`Settings` → `Secrets and variables` → `Actions` with the exact name
`OPENAI_API_KEY`. Rotating the repository secret and running a new deployment
replaces the key in the backend container.

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

Validate that the latest backup can actually be restored into an isolated,
temporary database:

```sh
docker compose run --rm --entrypoint /usr/local/bin/verify-backup-restore backup
```

This full restore check runs before every deployment and additionally every
Sunday through the `Verify Bazkit backup restore` workflow. The temporary
verification database is always removed afterwards. A failed restore stops the
deployment before migrations can modify production data.

Restoring a backup replaces database data and therefore remains an explicit
operator task. Stop the backend first, keep a second copy of the selected dump,
and validate the dump with `pg_restore --list` before restoring it.

Use a separate private R2 bucket for database backups and set its name as
`R2_BACKUP_BUCKET_NAME`. Never use the public media bucket for database dumps.
After a successful manual test, set `OFFSITE_BACKUP_ENABLED=True` and
`OFFSITE_BACKUP_REQUIRED=True`, so a missing upload configuration also stops a
deployment before migrations.

## Availability monitoring

The `Monitor Bazkit` GitHub Actions workflow checks `/health/` through the
public frontend every 15 minutes. Nginx forwards that single endpoint to the
backend, so the database is still checked without exposing Django's port 8000
to the internet.
The endpoint verifies both Django and its database connection. A failed check is
visible as a failed workflow run and can use the repository's normal GitHub
Actions notifications. Until a domain is available, the workflow uses the
server address stored in the existing `SERVER_HOST` repository secret.

## Application error monitoring

Backend exceptions, failed application e-mails and browser errors are grouped
in Django Admin under `Fehlerüberwachung`. Repeated occurrences increment a
counter and reopen a resolved issue instead of creating duplicates. The first
occurrence and later occurrences outside the configured cooldown send an alert
to `ERROR_ALERT_EMAIL`. Set `ERROR_MONITORING_ENABLED=False` only for local
development or an intentional maintenance window.
