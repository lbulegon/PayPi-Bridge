# PayPi-Bridge

Gateway de On/Off-Ramp para converter pagamentos em **Pi** em **moeda fiduciária (BRL)**, com confirmação via eventos blockchain (Soroban) e liquidação bancária via **Open Finance**.

## 🏗️ Arquitetura

```
Pi Wallet → Soroban Contract → CCIP/Relayer → Django Backend → Open Finance → Bancos
```

### Fluxo Completo

1. **DApp cria PaymentIntent** on-chain (Soroban) → emite evento
2. **Relayer (CCIP ou custom)** envia webhook assinado para `/webhooks/ccip`
3. **Backend valida** e inicia pagamento via **Open Finance** (Pix/Payments Initiation)
4. **Liquidação bancária** confirma → atualiza `PaymentIntent` para `SETTLED`
5. **Reconciliação** via `accounts/transactions` (Open Finance)

## 📁 Estrutura do Projeto

```
PayPi-Bridge/
├── backend/                    # Django + DRF backend
│   ├── app/
│   │   └── paypibridge/       # App principal
│   │       ├── models.py       # Models (PaymentIntent, Consent, etc.)
│   │       ├── views.py       # API endpoints
│   │       ├── serializers.py # DRF serializers
│   │       ├── urls.py        # URL routing
│   │       ├── clients/       # Clientes externos
│   │       │   ├── open_finance.py
│   │       │   └── pix.py
│   │       └── services/      # Serviços de negócio
│   │           └── pi_service.py  # Integração Pi Network
│   ├── tests/                 # Testes
│   └── requirements.txt       # Dependências Python (backend)
├── contracts/                 # Contratos Soroban
│   └── soroban/
│       └── paypi_bridge.rs   # Contrato principal
├── docs/                      # Documentação
│   ├── architecture.mmd      # Diagrama de arquitetura
│   ├── sequence.mmd          # Diagrama de sequência
│   └── REQUIREMENTS_SYNC.md  # Guia de sincronização de requirements
├── scripts/                   # Scripts utilitários
│   └── sync_requirements.py  # Sincroniza requirements.txt
├── sql/                       # Scripts SQL
│   └── schema.sql            # DDL inicial
├── openapi/                   # Especificação OpenAPI
│   └── openapi.yaml
├── postman/                   # Coleção Postman
├── requirements.txt          # Dependências Python (raiz - usado pelo Railway)
└── .env.example              # Variáveis de ambiente (template)
```

### ⚠️ Importante: Sincronização de Requirements

O Railway usa o `requirements.txt` da **raiz do projeto**, não o `backend/requirements.txt`.

**Sempre que adicionar uma dependência em `backend/requirements.txt`, execute:**

```bash
python scripts/sync_requirements.py
```

Isso garante que ambas as dependências estejam sincronizadas. Veja [docs/REQUIREMENTS_SYNC.md](docs/REQUIREMENTS_SYNC.md) para mais detalhes.

```

## 🚀 Quickstart (sem Docker)

O fluxo principal é **Python + PostgreSQL + Redis** na tua máquina (ou BD/Redis geridos na cloud, ex. Railway). Não é obrigatório usar Docker.

### Pré-requisitos

- Python 3.11+
- PostgreSQL 15+ (local ou URL remota)
- Redis (local em `127.0.0.1:6379` ou URL remota — usado pelo Celery para a fila de liquidação)

### 1. Configurar ambiente

```bash
cp .env.example .env
# Editar .env: DATABASE_URL ou DB_*, PI_*, CELERY_BROKER_URL, etc.
```

### 2. Backend local

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

pip install -r backend/requirements.txt
python scripts/sync_requirements.py   # alinha requirements.txt da raiz (Railway)

cd backend
python manage.py migrate
python manage.py runserver
```

### 3. Liquidação assíncrona (Celery)

Com `SETTLEMENT_ASYNC=1` (padrão), abre **outro terminal** com o mesmo venv:

```bash
cd backend
celery -A config worker -l info
```

Garante que o Redis da `CELERY_BROKER_URL` está a correr. Sem Redis: define `CELERY_TASK_ALWAYS_EAGER=1` ou `SETTLEMENT_ASYNC=0` (liquidação síncrona). Detalhes: [docs/SETTLEMENT_QUEUE.md](docs/SETTLEMENT_QUEUE.md).

**Pi Network:** o SDK pode exigir o repo noutro caminho (ex. pasta `PiNetwork`). Sem credenciais `PI_*`, a API responde mas `/api/pi/balance` pode devolver 503.

## 📡 API Endpoints

### PaymentIntent

- `POST /api/checkout/pi-intent` - Criar PaymentIntent
- `POST /api/payments/verify` - Verificar pagamento Pi

### Webhooks

- `POST /api/webhooks/ccip` - Webhook do relayer (HMAC)

### Payouts

- `POST /api/payouts/pix` - Criar pagamento Pix
- `POST /api/settlements/execute` - Liquidação automática Pi→BRL→Pix (após verify + consent)

### Pi Network

- `GET /api/pi/status` - Diagnóstico da integração Pi (env + SDK)
- `GET /api/pi/balance` - Obter saldo Pi da carteira do app
- `GET /api/payments/ledger/<txid>` - Auditoria da transação no Horizon (se configurado)
- `GET /health/bridge` - Saúde resumida (Pi API + Horizon / modo de confiança)

## 🔐 Segurança

- **Webhook HMAC**: Validação de assinatura em webhooks
- **Open Finance**: mTLS + OAuth2 + consents escopados
- **KYC/AML**: Verificação de identidade (planejado)
- **LGPD**: PII vault para dados pessoais (planejado)
- **Auditoria**: Logs de todas as operações (planejado)
- **Idempotência**: Prevenção de processamento duplicado

## 🧪 Testes

```bash
# Rodar todos os testes
cd backend
python manage.py test

# Rodar testes específicos
python manage.py test tests.paypibridge.test_models
python manage.py test tests.paypibridge.test_views

# Com cobertura
pip install coverage
coverage run --source='app' manage.py test
coverage report
```

## 📚 Documentação

- [Análise e Plano de Ação](./ANALISE_E_PLANO_ACAO.md) - Análise completa do projeto
- [Payment Trust Engine](./docs/PAYMENT_TRUST_ENGINE.md) - Pi Platform + Horizon opcional
- [Settlement Engine](./docs/SETTLEMENT_ENGINE.md) - Liquidação Pi → BRL → Pix
- [Fila Celery — liquidação](./docs/SETTLEMENT_QUEUE.md) - 202 Accepted, worker, Redis, dead letter
- [Diagramas](./docs/) - Arquitetura e sequência
- [OpenAPI](./openapi/openapi.yaml) - Especificação da API

## 🔗 Integrações

### Pi Network

O projeto integra com Pi Network usando o SDK `pi-python`:
- Autenticação de usuários
- Verificação de pagamentos
- Criação de pagamentos App-to-User
- Rastreamento de transações

### Open Finance

Integração com Open Banking Brasil:
- Payments Initiation API (Pix)
- Accounts/Transactions API (reconciliação)
- Consent Management

### Soroban (Stellar)

Contratos inteligentes para:
- PaymentIntent on-chain
- Eventos de confirmação
- Escrow e garantias

## 🛠️ Stack Tecnológica

- **Backend**: Django 5.0+ / Django REST Framework
- **Banco de Dados**: PostgreSQL
- **Cache/Fila**: Redis / Celery
- **Blockchain**: Soroban (Stellar)
- **Documentação**: drf-spectacular (OpenAPI)

## 📋 Status do Projeto

### ✅ Implementado

- Estrutura básica Django/DRF
- Models principais (PaymentIntent, Consent, PixTransaction)
- Endpoints básicos de API
- Integração Pi Network SDK
- Contratos Soroban (skeleton)
- Testes básicos
- Quickstart local (Postgres + Redis + Celery)

### ⚠️ Em Desenvolvimento

- Open Finance (implementação real)
- CCIP/Relayer
- Segurança e Compliance (KYC, LGPD)
- Monitoramento e observabilidade

### 📝 Planejado

- Testes de integração completos
- CI/CD
- Dashboard de monitoramento
- Documentação de deploy em produção

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está em desenvolvimento ativo. Consulte os arquivos de licença para mais informações.

## 🔗 Links Úteis

- [Pi Network Developer Portal](https://develop.pi)
- [Pi Platform Docs](../../docs/pi-platform-docs/)
- [Open Banking Brasil](https://www.bcb.gov.br/estabilidadefinanceira/openbanking)
- [Soroban Documentation](https://soroban.stellar.org/docs)

## 🆕 PPBridge Service

O projeto agora inclui o **PPBridge Service**, um engine completo de bridge entre criptomoedas e moedas fiduciárias:

- **State Machine**: Fluxo com estados validados (INITIATED → VALIDATED → BRIDGING → COMPLETED)
- **Adapters Desacoplados**: Interface clara para crypto e finance adapters
- **Idempotência**: Suporte completo via `Idempotency-Key` header
- **Webhooks Assinados**: HMAC SHA-256 com retry automático
- **Auditoria Completa**: Todos os eventos registrados
- **API REST**: Endpoints em `/api/v1/bridge/`

Veja [backend/app/bridge/README.md](backend/app/bridge/README.md) para documentação completa.

---

**Última atualização**: 2026-02-07
