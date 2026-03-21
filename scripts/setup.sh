#!/bin/bash
# Setup local (sem Docker): venv, dependências, migrações.
# Requer PostgreSQL e (opcional) Redis acessíveis conforme .env.

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "Setting up PayPi-Bridge (local)..."

if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    echo "Creating .env from .env.example — edita com DB_* / DATABASE_URL e PI_*"
    cp .env.example .env
  elif [ -f env.example ]; then
    cp env.example .env
  else
    echo "No .env.example found; create .env manually."
  fi
else
  echo ".env already exists"
fi

echo "Installing Python dependencies..."
cd backend
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
  python3 -m venv .venv
fi
if [ -d ".venv" ]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
else
  # shellcheck source=/dev/null
  source venv/bin/activate
fi
pip install -r requirements.txt
cd "$ROOT"
python3 scripts/sync_requirements.py 2>/dev/null || true

echo "Running migrations..."
cd backend
python manage.py migrate

echo "Done."
echo "  cd backend && source .venv/bin/activate  # ou venv"
echo "  python manage.py runserver"
echo "  # outro terminal: celery -A config worker -l info  (se SETTLEMENT_ASYNC=1)"
