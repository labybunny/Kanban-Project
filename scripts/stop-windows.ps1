$ErrorActionPreference = "Stop"

$containerName = "pm-mvp"
$existingContainer = docker ps -aq --filter "name=^${containerName}$"

if (-not $existingContainer) {
  Write-Host "Container $containerName is not running."
  exit 0
}

Write-Host "Stopping and removing container: $containerName"
docker rm -f $containerName | Out-Null
Write-Host "Container removed."
