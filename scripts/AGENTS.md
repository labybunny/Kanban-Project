# Scripts

This folder contains local Docker start/stop scripts for each target OS.

## Files

- `start-windows.ps1` / `stop-windows.ps1`
- `start-macos.sh` / `stop-macos.sh`
- `start-linux.sh` / `stop-linux.sh`

## Behavior

- Start scripts:
  - build Docker image `pm-mvp`
  - remove prior container named `pm-mvp` if it exists
  - run container on `http://localhost:8000`
  - load `.env` automatically when present
- Stop scripts:
  - stop and remove `pm-mvp` if running