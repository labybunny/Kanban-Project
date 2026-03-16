#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="pm-mvp"
EXISTING_CONTAINER="$(docker ps -aq --filter "name=^${CONTAINER_NAME}$")"

if [[ -z "${EXISTING_CONTAINER}" ]]; then
  echo "Container ${CONTAINER_NAME} is not running."
  exit 0
fi

echo "Stopping and removing container: ${CONTAINER_NAME}"
docker rm -f "${CONTAINER_NAME}" >/dev/null
echo "Container removed."
