#!/bin/sh
set -e

echo "=========================================================="
echo " Starting AgriLens Application Service"
echo " Image: ndoli/agrilens:latest"
echo " Time: $(date)"
echo "=========================================================="

# Run database migrations if configured
if [ "$AUTO_MIGRATE" = "true" ] || [ "$AUTO_MIGRATE" = "1" ]; then
    echo "==> Running database migrations..."
    python manage.py migrate --noinput
fi

# Collect static files if staticfiles directory is empty
if [ ! -d "/app/staticfiles" ] || [ -z "$(ls -A /app/staticfiles 2>/dev/null)" ]; then
    echo "==> Collecting static assets..."
    python manage.py collectstatic --noinput
fi

# Ensure AgriLens AI neural weights are present
mkdir -p /app/data/models
if [ "$DOWNLOAD_QWEN_MODEL" != "0" ] && [ "$DOWNLOAD_QWEN_MODEL" != "false" ]; then
    echo "==> Verifying AgriLens AI neural model weights (~2.1 GB)..."
    python scripts/download_qwen_model.py || echo "[WARN] AgriLens model download skipped/failed; background downloader will retry."
fi

echo "==> AgriLens initialization complete. Starting application server..."
exec "$@"

