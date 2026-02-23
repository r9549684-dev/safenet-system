#!/usr/bin/env bash
set -euo pipefail

echo "[1/6] Checking env file..."
if [ ! -f ".env" ]; then
  echo "ERROR: infra/.env not found. Copy from .env.example"
  exit 1
fi

echo "[2/6] Pulling base images..."
docker compose pull || true

echo "[3/6] Building and starting stack..."
docker compose up -d --build

echo "[4/6] Running migrations..."
docker compose exec -T api alembic upgrade head

echo "[5/6] Seeding default profiles/servers (idempotent)..."
docker compose exec -T api python -m app.seed

echo "[6/6] Health check..."
curl -fsS http://127.0.0.1:8500/health | cat
echo ""
echo "Done."