#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"
MOBILE_DIR="$ROOT_DIR/mobile/elettra_mobile"

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000/api/v1}"
ANDROID_API_BASE_URL="${ANDROID_API_BASE_URL:-http://10.0.2.2:8000/api/v1}"
IOS_API_BASE_URL="${IOS_API_BASE_URL:-$API_BASE_URL}"

RUN_PUB_GET="${RUN_PUB_GET:-true}"
RUN_ANALYZE="${RUN_ANALYZE:-true}"
RUN_TESTS="${RUN_TESTS:-true}"
BUILD_WEB="${BUILD_WEB:-true}"
BUILD_ANDROID_DEBUG="${BUILD_ANDROID_DEBUG:-true}"
BUILD_IOS_NO_CODESIGN="${BUILD_IOS_NO_CODESIGN:-false}"

cd "$MOBILE_DIR"

if [ "$RUN_PUB_GET" = "true" ]; then
  echo "==> Mobile: flutter pub get"
  flutter pub get
fi

if [ "$RUN_ANALYZE" = "true" ]; then
  echo "==> Mobile: flutter analyze"
  flutter analyze
fi

if [ "$RUN_TESTS" = "true" ]; then
  echo "==> Mobile: flutter test"
  flutter test
fi

if [ "$BUILD_WEB" = "true" ]; then
  echo "==> Mobile: flutter build web"
  flutter build web --dart-define=API_BASE_URL="$API_BASE_URL"
fi

if [ "$BUILD_ANDROID_DEBUG" = "true" ]; then
  echo "==> Mobile: flutter build apk --debug"
  flutter build apk --debug --dart-define=API_BASE_URL="$ANDROID_API_BASE_URL"
fi

if [ "$BUILD_IOS_NO_CODESIGN" = "true" ]; then
  echo "==> Mobile: flutter build ios --no-codesign"
  flutter build ios --no-codesign --dart-define=API_BASE_URL="$IOS_API_BASE_URL"
fi

echo "==> Mobile checks completed"
