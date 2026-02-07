#!/bin/bash
# Script para configurar ambiente e executar migrations no Railway
# Uso: ./scripts/setup_and_migrate.sh

set -e

echo "🚀 PayPi-Bridge - Setup e Migrations"
echo "======================================"

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

# Verificar se DATABASE_URL está configurada
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  AVISO: DATABASE_URL não está configurada no .env"
    echo "   Configure DATABASE_URL ou as variáveis DB_* individuais"
fi

# Verificar se Python está disponível
if ! command -v python3 &> /dev/null; then
    echo "❌ Erro: python3 não encontrado no PATH"
    exit 1
fi

# Verificar se pip está disponível
if ! command -v pip3 &> /dev/null; then
    echo "❌ Erro: pip3 não encontrado no PATH"
    exit 1
fi

# Instalar dependências (se necessário)
echo "📦 Verificando dependências..."
if ! python3 -c "import django" 2>/dev/null; then
    echo "   Instalando dependências do requirements.txt..."
    pip3 install -r requirements.txt
else
    echo "   ✓ Django já instalado"
fi

# Verificar conexão com o banco
echo ""
echo "🔌 Testando conexão com o banco de dados..."
python3 manage.py check --database default || {
    echo "❌ Erro ao conectar com o banco de dados"
    echo "   Verifique sua DATABASE_URL no .env"
    exit 1
}
echo "   ✓ Conexão OK!"

# Executar migrations
echo ""
echo "🗄️  Executando migrations..."
python3 manage.py migrate --verbosity=2

echo ""
echo "✅ Migrations concluídas com sucesso!"
echo ""
echo "Próximos passos:"
echo "  - Criar superusuário: python3 manage.py createsuperuser"
echo "  - Rodar servidor: python3 manage.py runserver"
echo "  - Ou usar: cd backend && python3 manage.py runserver"
