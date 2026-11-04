#!/usr/bin/env bash
# Usage: deploy/dump-railway.sh <output-file>. Runs on the laptop from the linked repo.
# pg_dump runs inside Railway's Postgres container, so no public proxy is needed.
set -euo pipefail

out="${1:?usage: dump-railway.sh <output-file>}"
umask 077
raw="$(mktemp)"
trap 'rm -f "$raw"' EXIT

railway ssh --service Postgres -- 'f=/tmp/bk.dump; pg_dump -U "$PGUSER" -d "$PGDATABASE" -Fc --no-owner --no-privileges -f $f && echo "SHA $(sha256sum $f | cut -d" " -f1)" && echo BEGIN && base64 -w0 $f && echo && echo END && rm -f $f' 2>/dev/null > "$raw"

remote_sha="$(grep '^SHA ' "$raw" | tr -d '\r' | cut -d' ' -f2)"
sed -n '/^BEGIN/,/^END/p' "$raw" | sed '1d;$d' | tr -d '\r\n' | base64 -d > "$out"
chmod 600 "$out"
local_sha="$(shasum -a 256 "$out" | cut -d' ' -f1)"

if [ -z "$remote_sha" ] || [ "$remote_sha" != "$local_sha" ]; then
    echo "checksum mismatch: remote=$remote_sha local=$local_sha" >&2
    rm -f "$out"
    exit 1
fi
echo "$out sha256=$local_sha"
