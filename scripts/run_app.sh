#!/usr/bin/env bash
set -euo pipefail

APP="project.app:app"
APP_DIR="src"
HOST="0.0.0.0"
PORT="8000"
DEFAULT_WORKERS=1
REDIS_WORKERS=4

# Match typical redis-server titles like "redis-server *:6379"
if pgrep -f "redis-server" >/dev/null 2>&1; then
  echo "Using redis with ${REDIS_WORKERS} workers"
  WORKERS="${REDIS_WORKERS}"
else
  echo "Using one worker"
  WORKERS="${DEFAULT_WORKERS}"
fi

exec uvicorn "${APP}" \
  --app-dir "${APP_DIR}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --workers "${WORKERS}"