#!/bin/bash
set -e

echo "Starting PayPi-Bridge..."

# Coletar static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Warning: collectstatic failed, continuing anyway..."

# Verificar se o logo foi coletado
if [ -f "staticfiles/paypibridge/img/logo.png" ]; then
    echo "✓ Logo encontrado em staticfiles/"
else
    echo "⚠ Logo não encontrado em staticfiles/, mas continuando..."
    # Tentar criar link simbólico se necessário
    mkdir -p staticfiles/paypibridge/img/ 2>/dev/null || true
    if [ -f "app/paypibridge/static/paypibridge/img/logo.png" ]; then
        cp app/paypibridge/static/paypibridge/img/logo.png staticfiles/paypibridge/img/logo.png 2>/dev/null || true
        echo "✓ Logo copiado manualmente"
    fi
fi

# Iniciar gunicorn
echo "Starting gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
