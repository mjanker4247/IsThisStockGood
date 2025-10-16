#!/usr/bin/env bash
set -euo pipefail

# Usage: tools/deploy_via_ssh.sh user@host [/path/to/app]
# Example: tools/deploy_via_ssh.sh ubuntu@myserver /opt/apps/IsThisStockGood

REMOTE_SSH_TARGET=${1:-}
REMOTE_PATH=${2:-}

if [[ -z "$REMOTE_SSH_TARGET" || -z "$REMOTE_PATH" ]]; then
  echo "Usage: $0 user@host /remote/path/to/repo"
  exit 1
fi

ssh -o BatchMode=yes -t "$REMOTE_SSH_TARGET" "bash -lc '
  set -euo pipefail
  cd "$REMOTE_PATH"
  echo "[deploy] Pulling latest..."
  git fetch --all --prune
  git reset --hard origin/master
  echo "[deploy] Building containers..."
  docker compose build --pull
  echo "[deploy] Restarting..."
  docker compose up -d
  echo "[deploy] Pruning old images..."
  docker image prune -f
  echo "[deploy] Done."
'"


