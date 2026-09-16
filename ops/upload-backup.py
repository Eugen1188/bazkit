import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3
from botocore.client import Config


def enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: upload-backup.py <backup-file>", file=sys.stderr)
        return 2

    if not enabled(os.getenv("OFFSITE_BACKUP_ENABLED", "false")):
        print("Off-site backup upload is disabled")
        return 0

    backup_path = Path(sys.argv[1])
    required = enabled(os.getenv("OFFSITE_BACKUP_REQUIRED", "false"))
    endpoint = os.getenv("R2_ENDPOINT_URL", "").strip()
    access_key = os.getenv("R2_ACCESS_KEY_ID", "").strip()
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY", "").strip()
    bucket = os.getenv("R2_BACKUP_BUCKET_NAME", "").strip()

    if not all((endpoint, access_key, secret_key, bucket)):
        message = "Off-site backup skipped because R2 is not fully configured"
        if required:
            print(message, file=sys.stderr)
            return 1
        print(message)
        return 0

    if not backup_path.is_file():
        print(f"Backup file does not exist: {backup_path}", file=sys.stderr)
        return 2

    prefix = os.getenv("R2_BACKUP_PREFIX", "database-backups").strip("/")
    object_key = f"{prefix}/{backup_path.name}" if prefix else backup_path.name
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )

    print(f"Uploading verified database backup to R2: {object_key}")
    client.upload_file(
        str(backup_path),
        bucket,
        object_key,
        ExtraArgs={"ContentType": "application/octet-stream"},
    )
    uploaded = client.head_object(Bucket=bucket, Key=object_key)
    if uploaded.get("ContentLength") != backup_path.stat().st_size:
        print("Uploaded backup size does not match the local file", file=sys.stderr)
        return 1

    retention_days = max(1, int(os.getenv("BACKUP_RETENTION_DAYS", "14")))
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    paginator = client.get_paginator("list_objects_v2")
    list_prefix = f"{prefix}/" if prefix else ""
    for page in paginator.paginate(Bucket=bucket, Prefix=list_prefix):
        for item in page.get("Contents", []):
            if item["LastModified"] < cutoff and item["Key"].endswith(".dump"):
                client.delete_object(Bucket=bucket, Key=item["Key"])
                print(f"Removed expired off-site backup: {item['Key']}")

    print(f"Off-site backup completed: {object_key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
