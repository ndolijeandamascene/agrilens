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

# Ensure AgriLens AI neural weights are present - verify before downloading
mkdir -p /app/data/models
MODEL_FILE="/app/data/models/qwen2.5-3b-instruct-q4_k_m.gguf"
ALT_MODEL_FILE="/app/models/qwen2.5-3b-instruct-q4_k_m.gguf"

if [ -f "$MODEL_FILE" ] && [ $(wc -c < "$MODEL_FILE" 2>/dev/null || echo 0) -ge 1900000000 ]; then
    echo "==> [OK] AgriLens AI neural model verified at $MODEL_FILE. Download skipped."
elif [ -f "$ALT_MODEL_FILE" ] && [ $(wc -c < "$ALT_MODEL_FILE" 2>/dev/null || echo 0) -ge 1900000000 ]; then
    echo "==> [OK] AgriLens AI neural model found at $ALT_MODEL_FILE. Linking to $MODEL_FILE..."
    ln -sf "$ALT_MODEL_FILE" "$MODEL_FILE"
elif [ "$DOWNLOAD_QWEN_MODEL" != "0" ] && [ "$DOWNLOAD_QWEN_MODEL" != "false" ]; then
    echo "==> No existing weights found on disk. Initiating download (~2.1 GB)..."
    python scripts/download_qwen_model.py || echo "[WARN] AgriLens model download skipped/failed; background downloader will retry."
else
    echo "==> Model download disabled (DOWNLOAD_QWEN_MODEL=$DOWNLOAD_QWEN_MODEL)."
fi

echo "==> AgriLens initialization complete. Starting application server..."
exec "$@"

