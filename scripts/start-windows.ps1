$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$imageName = "pm-mvp"
$containerName = "pm-mvp"

Write-Host "Building Docker image: $imageName"
docker build -t $imageName .

$existingContainer = docker ps -aq --filter "name=^${containerName}$"
if ($existingContainer) {
  Write-Host "Removing existing container: $containerName"
  docker rm -f $containerName | Out-Null
}

$runArgs = @("-d", "--name", $containerName, "-p", "8000:8000")
$envFile = Join-Path $repoRoot ".env"
if (Test-Path $envFile) {
  $runArgs += @("--env-file", $envFile)
}
$runArgs += $imageName

Write-Host "Starting container: $containerName"
docker run @runArgs | Out-Null

Write-Host "Server started at http://localhost:8000"
