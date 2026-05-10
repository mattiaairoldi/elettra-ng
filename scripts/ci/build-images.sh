#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"

cd "$ROOT_DIR"

GIT_SHA="$(git rev-parse --short=12 HEAD)"
IMAGE_NAME="${IMAGE_NAME:-elettra-api}"
IMAGE_TAG="${IMAGE_TAG:-sha-$GIT_SHA}"
REGISTRY="${REGISTRY:-}"
IMAGE_REPOSITORY="${IMAGE_REPOSITORY:-}"
PUSH="${PUSH:-false}"
TAG_LOCAL="${TAG_LOCAL:-true}"
EXTRA_TAGS="${EXTRA_TAGS:-}"
DOCKERFILE="${DOCKERFILE:-$ROOT_DIR/Dockerfile}"
BUILD_CONTEXT="${BUILD_CONTEXT:-$ROOT_DIR}"
DOCKER_BUILD_ARGS="${DOCKER_BUILD_ARGS:-}"

if [ -n "$REGISTRY" ]; then
  REGISTRY="${REGISTRY%/}"
fi

if [ -z "$IMAGE_REPOSITORY" ]; then
  if [ -n "$REGISTRY" ]; then
    IMAGE_REPOSITORY="$REGISTRY/$IMAGE_NAME"
  else
    IMAGE_REPOSITORY="$IMAGE_NAME"
  fi
fi

IMAGE_TAGS="$IMAGE_TAG"
if [ "$TAG_LOCAL" = "true" ] && [ -z "$REGISTRY" ]; then
  IMAGE_TAGS="$IMAGE_TAGS local"
fi
if [ -n "$EXTRA_TAGS" ]; then
  IMAGE_TAGS="$IMAGE_TAGS $EXTRA_TAGS"
fi

DOCKER_TAG_ARGS=""
for tag in $IMAGE_TAGS; do
  DOCKER_TAG_ARGS="$DOCKER_TAG_ARGS -t $IMAGE_REPOSITORY:$tag"
done

echo "==> Docker: build $IMAGE_REPOSITORY:$IMAGE_TAG"
docker build -f "$DOCKERFILE" $DOCKER_TAG_ARGS $DOCKER_BUILD_ARGS "$BUILD_CONTEXT"

if [ "$PUSH" = "true" ]; then
  echo "==> Docker: push image tags"
  for tag in $IMAGE_TAGS; do
    docker push "$IMAGE_REPOSITORY:$tag"
  done
fi

echo "==> Docker image refs"
for tag in $IMAGE_TAGS; do
  echo "$IMAGE_REPOSITORY:$tag"
done
