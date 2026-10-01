#!/bin/sh
set -eu

base_url="${1:-http://127.0.0.1:8080}"
base_url="${base_url%/}"
health_url="${2:-$base_url/health/}"
forwarded_proto="${3:-http}"
temporary_directory="$(mktemp -d)"

cleanup() {
  rm -rf "$temporary_directory"
}
trap cleanup EXIT INT TERM

curl --fail --silent --show-error --retry 3 --retry-all-errors \
  --connect-timeout 5 --max-time 20 \
  --header "X-Forwarded-Proto: $forwarded_proto" \
  "$health_url" >"$temporary_directory/health.json"
grep -q '"status": "healthy"' "$temporary_directory/health.json"

curl --fail --silent --show-error --retry 3 --retry-all-errors \
  --connect-timeout 5 --max-time 20 \
  "$base_url/" >"$temporary_directory/index.html"
grep -q '<app-root' "$temporary_directory/index.html"

curl --fail --silent --show-error --retry 3 --retry-all-errors \
  --connect-timeout 5 --max-time 20 \
  "$base_url/passwort-zuruecksetzen" >"$temporary_directory/reset.html"
grep -q '<app-root' "$temporary_directory/reset.html"

echo "Bazkit smoke test passed for $base_url"
