# Guia de Desenvolvimento - PayPi-Bridge

## Configuração do ambiente (local)

```bash
# 1. Dependências de sistema (exemplo Debian/Ubuntu)
sudo apt-get install -y postgresql-client python3-venv redis-server

# 2. PostgreSQL: criar BD e utilizador (ou usar DATABASE_URL remota)
# 3. Redis: garantir que corre em 127.0.0.1:6379 (ou ajustar CELERY_BROKER_URL)

# 4. Variáveis
cp .env.example .env
# Editar .env (DB_*, PI_*, CELERY_*)

# 5. venv e pacotes Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python scripts/sync_requirements.py

# 6. Migrações e servidor
cd backend
python manage.py migrate
python manage.py createsuperuser   # opcional
python manage.py runserver
```

### Worker Celery (liquidação assíncrona)

Noutro terminal, com o mesmo venv:

```bash
cd backend
celery -A config worker -l info
```

Ver [SETTLEMENT_QUEUE.md](./SETTLEMENT_QUEUE.md). Sem Redis local: `CELERY_TASK_ALWAYS_EAGER=1` ou `SETTLEMENT_ASYNC=0`.

## Estrutura de código

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

## Executando testes

```bash
cd backend
python manage.py test

python manage.py test tests.paypibridge.test_models
python manage.py test tests.paypibridge.test_views

pip install coverage
coverage run --source='app' manage.py test
coverage report
coverage html
```

## Integração Pi Network

O serviço `PiService` integra com o SDK `pi-python`:

```python
from app.paypibridge.services.pi_service import get_pi_service

pi_service = get_pi_service()

if pi_service.is_available():
    balance = pi_service.get_balance()
    payment = pi_service.verify_payment(payment_id)
    payment_id = pi_service.create_app_to_user_payment(
        user_uid="user_123",
        amount=Decimal("10.5"),
        memo="Payment description"
    )
```

## Variáveis de ambiente

### Obrigatórias (mínimo)

- `DJANGO_SECRET_KEY` ou `DJANGO_SECRET`
- Base de dados: `DATABASE_URL` ou `DB_*`

### Pi Network

- `PI_API_KEY`, `PI_WALLET_PRIVATE_SEED`, `PI_NETWORK`

### Opcionais

- `CCIP_WEBHOOK_SECRET`, Open Finance (`OF_*`), `FX_API_KEY`
- Celery: `CELERY_BROKER_URL`, `SETTLEMENT_ASYNC` — ver `.env.example`

## Banco de dados

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
```

O ficheiro `sql/schema.sql` é referência DDL; em desenvolvimento usa-se sobretudo **migrações Django**.

## Debugging

- Ajustar `LOG_LEVEL` / logging em `config/settings.py` ou variáveis do projeto.
- `python manage.py shell` para inspecionar models e serviços.

## Recursos adicionais

- [Análise e Plano de Ação](../ANALISE_E_PLANO_ACAO.md)
- [README Principal](../README.md)
- [Fila Celery / liquidação](./SETTLEMENT_QUEUE.md)
- Diagramas em `docs/architecture.mmd`, `docs/sequence.mmd`
