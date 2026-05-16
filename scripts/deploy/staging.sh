#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"
CONFIG_FILE="${DEPLOY_CONFIG:-$ROOT_DIR/deploy/staging.local.env}"
DRY_RUN=false

usage() {
  cat <<'EOF'
Usage: scripts/deploy/staging.sh [--config FILE] [--dry-run]

Deploys the versioned staging Compose files to a remote Ubuntu VPS and runs:
pull, migrate, up -d, ps.

Configuration is read from deploy/staging.local.env by default.
Copy deploy/staging.local.env.example and .env.staging.example before first use.
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
  echo "Copy deploy/staging.local.env.example to deploy/staging.local.env and fill it." >&2
  exit 1
fi

ENV_STAGING_IMAGE_REPOSITORY="${STAGING_IMAGE_REPOSITORY:-}"
ENV_STAGING_IMAGE_TAG="${STAGING_IMAGE_TAG:-}"
ENV_STAGING_DOMAIN="${STAGING_DOMAIN:-}"
ENV_STAGING_HEALTHCHECK_URL="${STAGING_HEALTHCHECK_URL:-}"
ENV_GIO_DOMAIN="${GIO_DOMAIN:-}"
ENV_GIO_SITE_ROOT="${GIO_SITE_ROOT:-}"

set -a
# shellcheck source=/dev/null
. "$CONFIG_FILE"
set +a

STAGING_IMAGE_REPOSITORY="${ENV_STAGING_IMAGE_REPOSITORY:-${STAGING_IMAGE_REPOSITORY:-}}"
STAGING_IMAGE_TAG="${ENV_STAGING_IMAGE_TAG:-${STAGING_IMAGE_TAG:-}}"
STAGING_DOMAIN="${ENV_STAGING_DOMAIN:-${STAGING_DOMAIN:-}}"
STAGING_HEALTHCHECK_URL="${ENV_STAGING_HEALTHCHECK_URL:-${STAGING_HEALTHCHECK_URL:-}}"
GIO_DOMAIN="${ENV_GIO_DOMAIN:-${GIO_DOMAIN:-}}"
GIO_SITE_ROOT="${ENV_GIO_SITE_ROOT:-${GIO_SITE_ROOT:-}}"

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
required STAGING_DOMAIN
required STAGING_IMAGE_REPOSITORY
required STAGING_IMAGE_TAG

STAGING_PORT="${STAGING_PORT:-22}"
STAGING_PROJECT_NAME="${STAGING_PROJECT_NAME:-elettra-staging}"
STAGING_APP_ENV_FILE="${STAGING_APP_ENV_FILE:-$ROOT_DIR/.env.staging}"
STAGING_UPLOAD_APP_ENV="${STAGING_UPLOAD_APP_ENV:-true}"
STAGING_BOOTSTRAP="${STAGING_BOOTSTRAP:-false}"
STAGING_REMOTE_SUDO="${STAGING_REMOTE_SUDO:-true}"
STAGING_DOCKER_SUDO="${STAGING_DOCKER_SUDO:-true}"
STAGING_REGISTRY_LOGIN_REQUIRED="${STAGING_REGISTRY_LOGIN_REQUIRED:-false}"
STAGING_UPLOAD_IMAGE="${STAGING_UPLOAD_IMAGE:-false}"
STAGING_UPLOAD_FLUTTER_WEB="${STAGING_UPLOAD_FLUTTER_WEB:-false}"
STAGING_FLUTTER_WEB_DIR="${STAGING_FLUTTER_WEB_DIR:-$ROOT_DIR/mobile/elettra_mobile/build/web}"
STAGING_PULL="${STAGING_PULL:-true}"
STAGING_RUN_MIGRATIONS="${STAGING_RUN_MIGRATIONS:-true}"
STAGING_SEED_DEMO="${STAGING_SEED_DEMO:-false}"
STAGING_RUN_HEALTHCHECK="${STAGING_RUN_HEALTHCHECK:-true}"
STAGING_HEALTHCHECK_URL="${STAGING_HEALTHCHECK_URL:-https://$STAGING_DOMAIN/api/v1/health}"

if [[ "$STAGING_APP_ENV_FILE" != /* ]]; then
  STAGING_APP_ENV_FILE="$ROOT_DIR/$STAGING_APP_ENV_FILE"
fi

if [[ "$STAGING_FLUTTER_WEB_DIR" != /* ]]; then
  STAGING_FLUTTER_WEB_DIR="$ROOT_DIR/$STAGING_FLUTTER_WEB_DIR"
fi

if [ "$STAGING_UPLOAD_APP_ENV" = "true" ] && [ ! -f "$STAGING_APP_ENV_FILE" ]; then
  echo "Missing staging app env file: $STAGING_APP_ENV_FILE" >&2
  echo "Copy .env.staging.example to .env.staging and fill secrets." >&2
  exit 1
fi

SSH_TARGET="$STAGING_USER@$STAGING_HOST"
SSH_OPTS=(-p "$STAGING_PORT" -o StrictHostKeyChecking=accept-new)
SCP_OPTS=(-P "$STAGING_PORT" -o StrictHostKeyChecking=accept-new)

if [ -n "${STAGING_SSH_KEY:-}" ]; then
  SSH_OPTS+=(-i "$STAGING_SSH_KEY")
  SCP_OPTS+=(-i "$STAGING_SSH_KEY")
fi

sq() {
  printf "'%s'" "$(printf "%s" "$1" | sed "s/'/'\\\\''/g")"
}

run_local() {
  echo "+ $*"
  if [ "$DRY_RUN" = "false" ]; then
    "$@"
  fi
}

upload_flutter_web() {
  local local_tar
  local remote_tar

  if [ ! -f "$STAGING_FLUTTER_WEB_DIR/index.html" ]; then
    echo "Missing Flutter web build: $STAGING_FLUTTER_WEB_DIR/index.html" >&2
    echo "Run: cd mobile/elettra_mobile && flutter build web --dart-define=API_BASE_URL=https://$STAGING_DOMAIN/api/v1" >&2
    exit 1
  fi

  local_tar="$(mktemp "${TMPDIR:-/tmp}/elettra-web.XXXXXX.tar.gz")"
  remote_tar="$STAGING_REMOTE_DIR/elettra-web.tar.gz"

  echo "+ tar -czf $local_tar -C $STAGING_FLUTTER_WEB_DIR ."
  if [ "$DRY_RUN" = "false" ]; then
    tar -czf "$local_tar" -C "$STAGING_FLUTTER_WEB_DIR" .
  fi

  copy_file "$local_tar" "$remote_tar"
  run_ssh "rm -rf $(sq "$STAGING_REMOTE_DIR/flutter-web") && mkdir -p $(sq "$STAGING_REMOTE_DIR/flutter-web") && tar -xzf $(sq "$remote_tar") -C $(sq "$STAGING_REMOTE_DIR/flutter-web") && rm -f $(sq "$remote_tar")"

  if [ "$DRY_RUN" = "false" ]; then
    rm -f "$local_tar"
  fi
}

run_ssh() {
  local command="$1"
  echo "+ ssh $SSH_TARGET $command"
  if [ "$DRY_RUN" = "false" ]; then
    ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "$command"
  fi
}

copy_file() {
  local src="$1"
  local dest="$2"
  echo "+ scp $src $SSH_TARGET:$dest"
  if [ "$DRY_RUN" = "false" ]; then
    scp "${SCP_OPTS[@]}" "$src" "$SSH_TARGET:$dest"
  fi
}

upload_image() {
  local image_ref="$STAGING_IMAGE_REPOSITORY:$STAGING_IMAGE_TAG"
  local local_tar
  local remote_tar

  local_tar="$(mktemp "${TMPDIR:-/tmp}/elettra-image.XXXXXX.tar")"
  remote_tar="$STAGING_REMOTE_DIR/elettra-image-$STAGING_IMAGE_TAG.tar"

  echo "+ docker save $image_ref -o $local_tar"
  if [ "$DRY_RUN" = "false" ]; then
    docker image inspect "$image_ref" >/dev/null
    docker save "$image_ref" -o "$local_tar"
  fi

  copy_file "$local_tar" "$remote_tar"
  run_ssh "$REMOTE_DOCKER load -i $(sq "$remote_tar") && rm -f $(sq "$remote_tar")"

  if [ "$DRY_RUN" = "false" ]; then
    rm -f "$local_tar"
  fi
}

remote_sudo_prefix() {
  if [ "$STAGING_REMOTE_SUDO" = "true" ]; then
    printf "sudo "
  fi
}

remote_docker_cmd() {
  if [ "$STAGING_DOCKER_SUDO" = "true" ]; then
    printf "sudo docker"
  else
    printf "docker"
  fi
}

REMOTE_SUDO="$(remote_sudo_prefix)"
REMOTE_DOCKER="$(remote_docker_cmd)"
REMOTE_DIR_Q="$(sq "$STAGING_REMOTE_DIR")"
REMOTE_ENV_Q="$(sq "$STAGING_REMOTE_DIR/.env.staging")"
REMOTE_DEPLOY_DIR_Q="$(sq "$STAGING_REMOTE_DIR/deploy")"

if [ "$STAGING_BOOTSTRAP" = "true" ]; then
  run_ssh "if ! command -v docker >/dev/null 2>&1; then sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin; fi; sudo systemctl enable --now docker"
fi

run_ssh "${REMOTE_SUDO}mkdir -p $REMOTE_DEPLOY_DIR_Q && ${REMOTE_SUDO}chown -R $(sq "$STAGING_USER"): $REMOTE_DIR_Q"

copy_file "$ROOT_DIR/deploy/compose.staging.yml" "$STAGING_REMOTE_DIR/deploy/compose.staging.yml"
copy_file "$ROOT_DIR/deploy/Caddyfile.staging" "$STAGING_REMOTE_DIR/deploy/Caddyfile.staging"

if [ "$STAGING_UPLOAD_FLUTTER_WEB" = "true" ]; then
  upload_flutter_web
fi

if [ "$STAGING_UPLOAD_APP_ENV" = "true" ]; then
  copy_file "$STAGING_APP_ENV_FILE" "$STAGING_REMOTE_DIR/.env.staging.tmp"
  run_ssh "mv $(sq "$STAGING_REMOTE_DIR/.env.staging.tmp") $REMOTE_ENV_Q && chmod 600 $REMOTE_ENV_Q"
else
  run_ssh "test -f $REMOTE_ENV_Q"
fi

env_lines=(
  "IMAGE_REPOSITORY=$STAGING_IMAGE_REPOSITORY"
  "IMAGE_TAG=$STAGING_IMAGE_TAG"
  "STAGING_DOMAIN=$STAGING_DOMAIN"
)
env_filter_names="IMAGE_REPOSITORY|IMAGE_TAG|STAGING_DOMAIN"

if [ -n "$GIO_DOMAIN" ]; then
  env_lines+=("GIO_DOMAIN=$GIO_DOMAIN")
  env_filter_names="${env_filter_names}|GIO_DOMAIN"
fi

if [ -n "$GIO_SITE_ROOT" ]; then
  env_lines+=("GIO_SITE_ROOT=$GIO_SITE_ROOT")
  env_filter_names="${env_filter_names}|GIO_SITE_ROOT"
fi

env_filter="^(${env_filter_names})="
printf_args=""
for line in "${env_lines[@]}"; do
  printf_args="$printf_args $(sq "$line")"
done

run_ssh "tmp=$(sq "$STAGING_REMOTE_DIR/.env.staging.next"); grep -v -E $(sq "$env_filter") $REMOTE_ENV_Q > \"\$tmp\"; printf '%s\n' $printf_args >> \"\$tmp\"; chmod 600 \"\$tmp\"; mv \"\$tmp\" $REMOTE_ENV_Q"

if [ -n "${STAGING_REGISTRY_SERVER:-}" ] && [ -n "${STAGING_REGISTRY_USERNAME:-}" ]; then
  if [ "$DRY_RUN" = "true" ]; then
    if [ -n "${STAGING_REGISTRY_PASSWORD_CMD:-}" ] || [ -n "${STAGING_REGISTRY_PASSWORD:-}" ]; then
      echo "+ docker login $STAGING_REGISTRY_SERVER"
    elif [ "$STAGING_REGISTRY_LOGIN_REQUIRED" = "true" ]; then
      echo "Registry login required but no password command/token was configured." >&2
      exit 1
    fi
  else
    REGISTRY_PASSWORD=""
    if [ -n "${STAGING_REGISTRY_PASSWORD_CMD:-}" ]; then
      REGISTRY_PASSWORD="$(eval "$STAGING_REGISTRY_PASSWORD_CMD")"
    elif [ -n "${STAGING_REGISTRY_PASSWORD:-}" ]; then
      REGISTRY_PASSWORD="$STAGING_REGISTRY_PASSWORD"
    fi

    if [ -n "$REGISTRY_PASSWORD" ]; then
      echo "+ docker login $STAGING_REGISTRY_SERVER"
      printf "%s" "$REGISTRY_PASSWORD" | ssh "${SSH_OPTS[@]}" "$SSH_TARGET" \
        "$REMOTE_DOCKER login $(sq "$STAGING_REGISTRY_SERVER") -u $(sq "$STAGING_REGISTRY_USERNAME") --password-stdin"
    elif [ "$STAGING_REGISTRY_LOGIN_REQUIRED" = "true" ]; then
      echo "Registry login required but no password command/token was configured." >&2
      exit 1
    fi
  fi
elif [ "$STAGING_REGISTRY_LOGIN_REQUIRED" = "true" ]; then
  echo "Registry login required but STAGING_REGISTRY_SERVER/USERNAME are missing." >&2
  exit 1
fi

if [ "$STAGING_UPLOAD_IMAGE" = "true" ]; then
  upload_image
  STAGING_PULL=false
fi

compose_base="cd $REMOTE_DIR_Q && $REMOTE_DOCKER compose --env-file .env.staging -p $(sq "$STAGING_PROJECT_NAME") -f deploy/compose.staging.yml"

if [ "$STAGING_PULL" = "true" ]; then
  run_ssh "$compose_base pull"
fi

if [ "$STAGING_RUN_MIGRATIONS" = "true" ]; then
  run_ssh "$compose_base run --rm web uv run python manage.py migrate --noinput"
fi

if [ "$STAGING_SEED_DEMO" = "true" ]; then
  run_ssh "$compose_base run --rm web uv run python manage.py seed_diagnostic_chapters"
  run_ssh "$compose_base run --rm web uv run python manage.py seed_mvp_demo"
fi

run_ssh "$compose_base up -d --remove-orphans"
run_ssh "$compose_base restart caddy"
run_ssh "$compose_base ps"

if [ "$STAGING_RUN_HEALTHCHECK" = "true" ]; then
  run_local curl -fsS "$STAGING_HEALTHCHECK_URL"
  echo
fi

echo "Staging deploy completed: $STAGING_IMAGE_REPOSITORY:$STAGING_IMAGE_TAG"
