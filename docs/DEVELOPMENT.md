# Guia de Desenvolvimento - PayPi-Bridge

## 🛠️ Configuração do Ambiente

### Opção 1: Docker (Recomendado)

```bash
# 1. Configurar variáveis de ambiente
cp env.example .env
# Editar .env com suas credenciais

# 2. Iniciar serviços
docker-compose up -d

# 3. Ver logs
docker-compose logs -f backend

# 4. Acessar API
curl http://localhost:9080/api/pi/balance
```

### Opção 2: Desenvolvimento Local

```bash
# 1. Instalar dependências do sistema
sudo apt-get install postgresql-client python3-venv

# 2. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependências Python
cd backend
pip install -r requirements.txt

# 4. Configurar banco (usar Docker para PostgreSQL)
docker-compose up -d db redis

# 5. Configurar .env
cp ../env.example ../.env
# Editar .env

# 6. Rodar migrações
python manage.py migrate

# 7. Criar superusuário
python manage.py createsuperuser

# 8. Rodar servidor
python manage.py runserver
```

## 📝 Estrutura de Código

### Models

Os models principais estão em `backend/app/paypibridge/models.py`:

- **PaymentIntent**: Intenção de pagamento Pi → BRL
- **Consent**: Consentimentos Open Finance
- **BankAccount**: Contas bancárias vinculadas
- **PixTransaction**: Transações Pix criadas
- **Escrow**: Garantias e escrow

### Views

As views da API estão em `backend/app/paypibridge/views.py`:

- `IntentView`: Criar PaymentIntent
- `VerifyPiPaymentView`: Verificar pagamento Pi
- `CCIPWebhookView`: Webhook do relayer
- `PixPayoutView`: Criar pagamento Pix
- `PiBalanceView`: Obter saldo Pi

### Services

Serviços de negócio em `backend/app/paypibridge/services/`:

- `pi_service.py`: Integração com Pi Network SDK

### Clients

Clientes externos em `backend/app/paypibridge/clients/`:

- `open_finance.py`: Cliente Open Finance (placeholder)
- `pix.py`: Wrapper para Pix via Open Finance

## 🧪 Executando Testes

```bash
# Todos os testes
python manage.py test

# Testes específicos
python manage.py test tests.paypibridge.test_models
python manage.py test tests.paypibridge.test_views

# Com cobertura
pip install coverage
coverage run --source='app' manage.py test
coverage report
coverage html  # Gera relatório HTML
```

## 🔌 Integração Pi Network

O serviço `PiService` integra com o SDK `pi-python`:

```python
from app.paypibridge.services.pi_service import get_pi_service

pi_service = get_pi_service()

# Verificar disponibilidade
if pi_service.is_available():
    # Obter saldo
    balance = pi_service.get_balance()
    
    # Verificar pagamento
    payment = pi_service.verify_payment(payment_id)
    
    # Criar pagamento A2U
    payment_id = pi_service.create_app_to_user_payment(
        user_uid="user_123",
        amount=Decimal("10.5"),
        memo="Payment description"
    )
```

## 🔐 Variáveis de Ambiente

Principais variáveis necessárias:

### Obrigatórias

- `PI_API_KEY`: API key da Pi Network
- `PI_WALLET_PRIVATE_SEED`: Seed privada da carteira
- `PI_NETWORK`: "Pi Network" ou "Pi Testnet"
- `SECRET_KEY`: Django secret key
- `DB_PASSWORD`: Senha do PostgreSQL

### Opcionais (para funcionalidades específicas)

- `CCIP_WEBHOOK_SECRET`: Secret para validar webhooks
- `OF_CLIENT_ID`: Cliente Open Finance
- `OF_CLIENT_SECRET`: Secret Open Finance
- `FX_API_KEY`: API key para câmbio

## 📊 Banco de Dados

### Migrações

```bash
# Criar migração
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Ver status
python manage.py showmigrations
```

### Schema SQL

O schema inicial está em `sql/schema.sql` e é aplicado automaticamente pelo Docker.

## 🐛 Debugging

### Logs

```bash
# Logs do Docker
docker-compose logs -f backend

# Logs do Django (desenvolvimento)
# Configurar LOG_LEVEL=DEBUG no .env
```

### Django Shell

```bash
python manage.py shell

# Exemplo de uso
from app.paypibridge.models import PaymentIntent
from app.paypibridge.services.pi_service import get_pi_service

# Listar intents
PaymentIntent.objects.all()

# Testar Pi service
pi_service = get_pi_service()
pi_service.get_balance()
```

## 📚 Recursos Adicionais

- [Análise e Plano de Ação](../ANALISE_E_PLANO_ACAO.md)
- [README Principal](../README.md)
- [Diagramas](./architecture.mmd, ./sequence.mmd)
