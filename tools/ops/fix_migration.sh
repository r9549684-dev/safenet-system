#!/bin/bash
set -e

echo "=== Current alembic_version ==="
docker exec infra-db-1 psql -U safenet safenet -c "SELECT version_num FROM alembic_version;"

echo "=== Resetting to 0001_init ==="
docker exec infra-db-1 psql -U safenet safenet -c "UPDATE alembic_version SET version_num='0001_init';"

echo "=== After reset ==="
docker exec infra-db-1 psql -U safenet safenet -c "SELECT version_num FROM alembic_version;"

echo "=== Alembic upgrade head ==="
docker exec infra-api-1 alembic upgrade head

echo "=== Final alembic current ==="
docker exec infra-api-1 alembic current

echo "=== Verify user_connections table ==="
docker exec infra-db-1 psql -U safenet safenet -c "\d user_connections"

echo "=== DONE ==="
