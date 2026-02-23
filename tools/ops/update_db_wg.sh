#!/bin/bash
set -e

SERVER_PUBLIC=$(cat /etc/wireguard/server_public.key)
echo "=== Updating servers meta with wg_public_key ==="
echo "Key: $SERVER_PUBLIC"

# Обновляем meta JSON для всех трёх серверов (все на одном хосте)
docker exec infra-db-1 psql -U safenet safenet -c \
  "UPDATE servers SET meta = (meta::jsonb || jsonb_build_object('wg_public_key', '$SERVER_PUBLIC'))::json WHERE id IN (1,2,3);"

# Проверка
docker exec infra-db-1 psql -U safenet safenet -c \
  "SELECT id, country, name, meta FROM servers ORDER BY id;"

echo "=== Clearing stale user_connections (will be regenerated with real key) ==="
docker exec infra-db-1 psql -U safenet safenet -c \
  "DELETE FROM user_connections;"

echo "=== Restarting API container ==="
cd /opt/safenet-v2/infra
docker compose restart api
sleep 3
docker ps --format "table {{.Names}}\t{{.Status}}"

echo "=== DONE ==="
