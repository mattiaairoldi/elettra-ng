#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"
CONFIG_FILE="${DEPLOY_CONFIG:-$ROOT_DIR/deploy/staging.local.env}"
DRY_RUN=false

usage() {
  cat <<'EOF'
Usage: scripts/deploy/bootstrap-vps.sh [--config FILE] [--dry-run]

Prepares a disposable/staging Ubuntu VPS for the Docker-based Elettra deploy.
It connects as root, installs Docker, adds the deploy user to the docker group,
creates the remote deploy directory, and optionally stops/disables host services
that collide with the Docker stack.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --config)
      if [ "$#" -lt 2 ]; then
        echo "Missing value for --config" >&2
        usage >&2
        exit 2
      fi
      CONFIG_FILE="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Missing deploy config: $CONFIG_FILE" >&2
  exit 1
fi

set -a
# shellcheck source=/dev/null
. "$CONFIG_FILE"
set +a

required() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    echo "Missing required config: $name" >&2
    exit 1
  fi
}

required STAGING_HOST
required STAGING_USER
required STAGING_REMOTE_DIR

STAGING_PORT="${STAGING_PORT:-22}"
STAGING_ROOT_USER="${STAGING_ROOT_USER:-root}"
STAGING_STOP_LEGACY_SERVICES="${STAGING_STOP_LEGACY_SERVICES:-true}"
STAGING_LEGACY_SUPERVISOR_PROGRAM="${STAGING_LEGACY_SUPERVISOR_PROGRAM:-elettra}"
STAGING_DISABLE_SERVICES="${STAGING_DISABLE_SERVICES:-postgresql nginx supervisor}"
STAGING_COPY_ROOT_AUTHORIZED_KEYS="${STAGING_COPY_ROOT_AUTHORIZED_KEYS:-true}"

SSH_TARGET="$STAGING_ROOT_USER@$STAGING_HOST"
SSH_OPTS=(-p "$STAGING_PORT" -o StrictHostKeyChecking=accept-new)

if [ -n "${STAGING_SSH_KEY:-}" ]; then
  SSH_OPTS+=(-i "$STAGING_SSH_KEY")
fi

sq() {
  printf "'%s'" "$(printf "%s" "$1" | sed "s/'/'\\\\''/g")"
}

run_ssh() {
  local command="$1"
  echo "+ ssh $SSH_TARGET $command"
  if [ "$DRY_RUN" = "false" ]; then
    ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "$command"
  fi
}

remote_script=$(cat <<EOF
set -Eeuo pipefail

if ! id $(sq "$STAGING_USER") >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash $(sq "$STAGING_USER")
fi

apt-get update
if apt-cache show docker-compose-plugin >/dev/null 2>&1; then
  apt-get install -y docker.io docker-compose-plugin
else
  apt-get install -y docker.io docker-compose-v2
fi
systemctl enable --now docker
usermod -aG docker $(sq "$STAGING_USER")

mkdir -p $(sq "$STAGING_REMOTE_DIR")
chown -R $(sq "$STAGING_USER"):$(sq "$STAGING_USER") $(sq "$STAGING_REMOTE_DIR")

if [ $(sq "$STAGING_COPY_ROOT_AUTHORIZED_KEYS") = "true" ] && [ -f /root/.ssh/authorized_keys ]; then
  install -d -m 700 -o $(sq "$STAGING_USER") -g $(sq "$STAGING_USER") /home/$(sq "$STAGING_USER")/.ssh
  install -m 600 -o $(sq "$STAGING_USER") -g $(sq "$STAGING_USER") /root/.ssh/authorized_keys /home/$(sq "$STAGING_USER")/.ssh/authorized_keys
fi

if [ $(sq "$STAGING_STOP_LEGACY_SERVICES") = "true" ]; then
  if command -v supervisorctl >/dev/null 2>&1; then
    supervisorctl stop $(sq "$STAGING_LEGACY_SUPERVISOR_PROGRAM") || true
  fi
  for service in $STAGING_DISABLE_SERVICES; do
    systemctl stop "\$service" 2>/dev/null || true
    systemctl disable "\$service" 2>/dev/null || true
  done
fi

docker --version
docker compose version
id $(sq "$STAGING_USER")
EOF
)

run_ssh "$remote_script"
