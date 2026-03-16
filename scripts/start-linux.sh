#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

IMAGE_NAME="pm-mvp"
CONTAINER_NAME="pm-mvp"

echo "Building Docker image: ${IMAGE_NAME}"
docker build -t "${IMAGE_NAME}" .

EXISTING_CONTAINER="$(docker ps -aq --filter "name=^${CONTAINER_NAME}$")"
if [[ -n "${EXISTING_CONTAINER}" ]]; then
  echo "Removing existing container: ${CONTAINER_NAME}"
  docker rm -f "${CONTAINER_NAME}" >/dev/null
fi

if [[ -f "${REPO_ROOT}/.env" ]]; then
  docker run -d --name "${CONTAINER_NAME}" --env-file "${REPO_ROOT}/.env" -p 8000:8000 "${IMAGE_NAME}" >/dev/null
else
  docker run -d --name "${CONTAINER_NAME}" -p 8000:8000 "${IMAGE_NAME}" >/dev/null
fi

echo "Server started at http://localhost:8000"
