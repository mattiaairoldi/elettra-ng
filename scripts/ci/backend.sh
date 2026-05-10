#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"

cd "$ROOT_DIR"

PYTEST_ARGS="${PYTEST_ARGS:--q}"
SCHEMA_FILE="${SCHEMA_FILE:-/tmp/elettra-schema.yml}"

echo "==> Backend: pytest ${PYTEST_ARGS}"
docker compose run --rm web uv run pytest ${PYTEST_ARGS}

echo "==> Backend: migration drift check"
docker compose run --rm web uv run python manage.py makemigrations --check --dry-run

echo "==> Backend: OpenAPI validation"
docker compose run --rm web uv run python manage.py spectacular --validate --fail-on-warn --file "$SCHEMA_FILE"

echo "==> Backend checks completed"
