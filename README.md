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
│   ├── requirements.txt       # Dependências Python (backend)
│   └── Dockerfile            # Container Docker
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
├── docker-compose.yml        # Orquestração Docker
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

## 🚀 Quickstart

### Pré-requisitos

- Docker e Docker Compose
- Python 3.11+ (para desenvolvimento local)
- PostgreSQL 15+
- Redis (para cache e Celery)

### 1. Configurar Ambiente

```bash
# Copiar variáveis de ambiente
cp .env.example .env

# Editar .env com suas credenciais
# - PI_API_KEY
# - PI_WALLET_PRIVATE_SEED
# - DB_PASSWORD
# - CCIP_WEBHOOK_SECRET
# - Open Finance credentials
```

### 2. Iniciar com Docker

O backend PayPi-Bridge sobe na **porta 9080** (evita conflito com Core_sinapUm e outros na 8000/8001).

```bash
# Iniciar todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f backend

# API: http://localhost:9080/api/ | Health: http://localhost:9080/health/

# Parar serviços
docker-compose down
```

### 3. Desenvolvimento Local

```bash
# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r backend/requirements.txt

# Subir só DB e Redis (opcional)
docker-compose up -d db redis

# Variáveis: copiar .env.example para .env e preencher DB_* e PI_* se quiser Pi Network

# Rodar migrações (a partir da pasta backend)
cd backend
python manage.py migrate

# Criar superusuário (opcional)
python manage.py createsuperuser

# Rodar servidor de desenvolvimento
python manage.py runserver
```

**Nota:** A integração com Pi Network usa o SDK em `PiNetwork/sdk/pi-python`. Para funcionar em desenvolvimento local, o repositório deve estar em uma pasta que contenha `PiNetwork` (ex.: `.../PiNetwork/projects/PayPi-Bridge`). No Docker, o SDK não é copiado por padrão; a API responde normalmente e o endpoint `/api/pi/balance` retorna 503 se o Pi não estiver configurado.

## 📡 API Endpoints

### PaymentIntent

- `POST /api/checkout/pi-intent` - Criar PaymentIntent
- `POST /api/payments/verify` - Verificar pagamento Pi

### Webhooks

- `POST /api/webhooks/ccip` - Webhook do relayer (HMAC)

### Payouts

- `POST /api/payouts/pix` - Criar pagamento Pix

### Pi Network

- `GET /api/pi/balance` - Obter saldo Pi da carteira do app

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
- **Containerização**: Docker / Docker Compose
- **Documentação**: drf-spectacular (OpenAPI)

## 📋 Status do Projeto

### ✅ Implementado

- Estrutura básica Django/DRF
- Models principais (PaymentIntent, Consent, PixTransaction)
- Endpoints básicos de API
- Integração Pi Network SDK
- Contratos Soroban (skeleton)
- Testes básicos
- Docker Compose para desenvolvimento

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
