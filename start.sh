#!/usr/bin/env bash
set -euo pipefail
# Behind Railway's proxy, trust X-Forwarded-Proto so url_for builds https:// asset links.
exec uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips "*"
