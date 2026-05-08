#!/bin/sh
set -eu

wait_for_tcp() {
  name="$1"
  host="$2"
  port="$3"

  echo "Waiting for ${name} at ${host}:${port}..."
  until nc -z "$host" "$port"; do
    sleep 1
  done
}

if [ -n "${POSTGRES_HOST:-}" ]; then
  wait_for_tcp "PostgreSQL" "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}"
fi

if [ -n "${REDIS_HOST:-redis}" ]; then
  wait_for_tcp "Redis" "${REDIS_HOST:-redis}" "${REDIS_PORT:-6379}"
fi

if [ -n "${MINIO_HOST:-minio}" ]; then
  wait_for_tcp "MinIO" "${MINIO_HOST:-minio}" "${MINIO_PORT:-9000}"
fi

exec "$@"

