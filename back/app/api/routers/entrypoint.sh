#!/bin/sh
set -e  # Exit on error

echo "Starting application..."

# Aplica las migraciones
echo "Running database migrations..."
/app/.venv/bin/alembic upgrade head

# Inicia el servidor de FastAPI
echo "Starting FastAPI server..."

# Detecta el entorno (por defecto: development)
ENV=${ENVIRONMENT:-development}

if [ "$ENV" = "production" ]; then
    echo "🚀 Running in PRODUCTION mode"
    exec fastapi run app/main.py
else
    echo "👾 Running in DEVELOPMENT mode (with auto-reload)"
    exec fastapi dev app/main.py --host 0.0.0.0 --port 8000
fi
