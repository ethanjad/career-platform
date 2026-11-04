#!/usr/bin/env bash
# Usage: deploy/deploy.sh <git-ref>. Runs on the server. Rolls back if /healthz never returns 200.
set -euo pipefail

ref="${1:?usage: deploy.sh <git-ref>}"
cd /opt/career-platform

healthy() {
    for _ in $(seq 1 30); do
        [ "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/healthz)" = "200" ] && return 0
        sleep 1
    done
    return 1
}

switch_to() {
    git checkout --quiet --detach "$1"
    uv sync --locked --quiet
    sudo systemctl restart career-platform
}

previous="$(git rev-parse HEAD)"
git fetch --quiet --prune origin
switch_to "origin/$ref"

if healthy; then
    echo "deployed $(git rev-parse --short HEAD)"
else
    echo "healthz failed on $ref; rolling back to ${previous:0:7}" >&2
    switch_to "$previous"
    healthy || echo "rollback is unhealthy too" >&2
    exit 1
fi
