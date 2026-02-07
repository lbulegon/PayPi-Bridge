#!/bin/bash
# Script para criar superusuário Django
# Uso: ./scripts/create_superuser.sh

set -e

echo "👤 PayPi-Bridge - Criar Superusuário"
echo "====================================="

# Navegar para o diretório backend
cd "$(dirname "$0")/../backend" || exit 1

# Verificar se o .env existe
if [ ! -f "../.env" ]; then
    echo "⚠️  AVISO: Arquivo .env não encontrado!"
    echo "   Copie .env.example para .env e configure as variáveis."
    exit 1
fi

# Carregar variáveis do .env
if [ -f "../.env" ]; then
    echo "📋 Carregando variáveis do .env..."
    set -a
    source ../.env
    set +a
fi

# Verificar se Python está disponível
if ! command -v python3 &> /dev/null; then
    echo "❌ Erro: python3 não encontrado no PATH"
    exit 1
fi

# Verificar se está em ambiente virtual (opcional)
if [ -d "venv" ]; then
    echo "🔧 Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Verificar conexão com o banco
echo ""
echo "🔌 Verificando conexão com o banco de dados..."
python3 manage.py check --database default || {
    echo "❌ Erro ao conectar com o banco de dados"
    echo "   Verifique sua DATABASE_URL no .env"
    exit 1
}
echo "   ✓ Conexão OK!"

# Verificar se já existe superusuário
echo ""
echo "🔍 Verificando superusuários existentes..."
SUPERUSERS=$(python3 manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).count())" 2>/dev/null || echo "0")

if [ "$SUPERUSERS" != "0" ]; then
    echo "   ⚠️  Já existem $SUPERUSERS superusuário(s) no sistema"
    read -p "   Deseja criar outro? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "   Operação cancelada."
        exit 0
    fi
fi

# Verificar se há variáveis de ambiente configuradas
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo ""
    echo "📝 Usando credenciais das variáveis de ambiente..."
    python3 manage.py createsuperuser \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "$DJANGO_SUPERUSER_EMAIL" \
        --password "$DJANGO_SUPERUSER_PASSWORD" \
        --noinput
else
    echo ""
    echo "📝 Modo interativo..."
    echo "   (Para usar variáveis de ambiente, configure no .env:)"
    echo "   DJANGO_SUPERUSER_USERNAME=admin"
    echo "   DJANGO_SUPERUSER_EMAIL=admin@example.com"
    echo "   DJANGO_SUPERUSER_PASSWORD=senha_segura"
    echo ""
    python3 manage.py createsuperuser
fi

echo ""
echo "✅ Superusuário criado com sucesso!"
echo ""
echo "Próximos passos:"
echo "  - Acesse o admin: http://localhost:8000/admin/"
echo "  - Faça login com as credenciais criadas"
