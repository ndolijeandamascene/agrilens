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

# Check or download Qwen 2.5 3B neural model if configured
if [ "$DOWNLOAD_QWEN_MODEL" = "true" ] || [ "$DOWNLOAD_QWEN_MODEL" = "1" ]; then
    echo "==> Checking Qwen 2.5 3B neural model weights..."
    python scripts/download_qwen_model.py || echo "[WARN] Qwen model download skipped/failed; continuing in deterministic grounded mode."
fi

echo "==> AgriLens initialization complete. Starting application server..."
exec "$@"

