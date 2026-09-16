FROM postgres:16-alpine

RUN apk add --no-cache python3 py3-pip \
    && python3 -m venv /opt/backup-venv \
    && /opt/backup-venv/bin/pip install --no-cache-dir 'boto3==1.34.162'

COPY ops/upload-backup.py /usr/local/bin/upload-backup.py
