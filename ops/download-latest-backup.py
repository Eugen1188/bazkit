import os
import sys
from pathlib import Path

import boto3
from botocore.client import Config


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: download-latest-backup.py <target-file>", file=sys.stderr)
        return 2

    endpoint = os.getenv("R2_ENDPOINT_URL", "").strip()
    access_key = os.getenv("R2_ACCESS_KEY_ID", "").strip()
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY", "").strip()
    bucket = os.getenv("R2_BACKUP_BUCKET_NAME", "").strip()
    if not all((endpoint, access_key, secret_key, bucket)):
        print("Off-site backup storage is not fully configured", file=sys.stderr)
        return 1

    prefix = os.getenv("R2_BACKUP_PREFIX", "database-backups").strip("/")
    list_prefix = f"{prefix}/" if prefix else ""
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )
    objects = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=list_prefix):
        objects.extend(
            item for item in page.get("Contents", [])
            if item["Key"].endswith(".dump")
        )
    if not objects:
        print("No off-site database backup found", file=sys.stderr)
        return 1

    latest = max(objects, key=lambda item: item["LastModified"])
    target = Path(sys.argv[1])
    target.parent.mkdir(parents=True, exist_ok=True)
    client.download_file(bucket, latest["Key"], str(target))
    if target.stat().st_size != latest["Size"]:
        print("Downloaded backup size does not match the off-site object", file=sys.stderr)
        return 1
    print(f"Downloaded off-site backup for restore verification: {latest['Key']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
