#!/bin/sh
# Local Docker entrypoint: equivalent to `make setup` + optional demo data + API.
set -e

echo "==> Running migrations..."
alembic upgrade head

echo "==> Seeding configuration..."
python scripts/seed_config.py

echo "==> Ensuring admin user..."
python scripts/create_user.py \
  --username "${ADMIN_USERNAME:-admin}" \
  --password "${ADMIN_PASSWORD:-tu-password}" \
  --nombre-display "${ADMIN_DISPLAY_NAME:-Admin}"

if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  echo "==> Seeding demo data..."
  python scripts/seed_demo_data.py
fi

echo "==> Starting API..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
