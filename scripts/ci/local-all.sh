#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

RUN_BACKEND="${RUN_BACKEND:-true}"
RUN_MOBILE="${RUN_MOBILE:-true}"
RUN_BUILD_IMAGES="${RUN_BUILD_IMAGES:-true}"

if [ "$RUN_BACKEND" = "true" ]; then
  "$SCRIPT_DIR/backend.sh"
fi

if [ "$RUN_MOBILE" = "true" ]; then
  "$SCRIPT_DIR/mobile.sh"
fi

if [ "$RUN_BUILD_IMAGES" = "true" ]; then
  "$SCRIPT_DIR/build-images.sh"
fi

echo "==> Local CI completed"
