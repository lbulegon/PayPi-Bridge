# PPBridge Service

Serviço completo de bridge entre criptomoedas e moedas fiduciárias, implementado como app Django integrado ao PayPi-Bridge.

## 🏗️ Arquitetura

```
Client → API → Flow Engine → Adapters → External Services
                ↓
            State Machine
                ↓
            Event Audit
                ↓
            Webhooks
```

## 📋 Componentes

### 1. Models (`models.py`)
- **BridgeFlow**: Fluxo de bridge principal
- **FlowEvent**: Eventos de auditoria
- **IdempotencyRecord**: Registros de idempotência
- **WebhookDelivery**: Entregas de webhook

### 2. Flow Engine (`flow/engine.py`)
- State machine com estados: INITIATED → VALIDATED → BRIDGING → COMPLETED
- Transições validadas
- Eventos registrados para cada transição
- Tratamento de erros com rollback

### 3. Adapters (`adapters/`)
- **CryptoAdapter**: Interface para criptomoedas (source)
- **FinanceAdapter**: Interface para moedas fiduciárias (target)
- Implementações stub:
  - `PiNetworkStubAdapter`: Mock para Pi Network
  - `PixStubAdapter`: Mock para Pix

### 4. Webhooks (`webhooks/`)
- Assinatura HMAC SHA-256
- Retry com backoff (1s, 5s, 15s)
- Auditoria completa de entregas

### 5. API (`api/views.py`)
- REST API com DRF
- Idempotência via `Idempotency-Key` header
- Autenticação opcional via `X-API-Key`

## 🚀 Endpoints

### POST /api/v1/bridge/flows/
Cria um novo flow de bridge.

**Headers:**
- `X-API-Key`: API key (se habilitado)
- `Idempotency-Key`: UUID para idempotência (opcional)

**Body:**
```json
{
  "source": {
    "domain": "crypto",
    "adapter": "pi_network"
  },
  "target": {
    "domain": "finance",
    "adapter": "pix"
  },
  "asset": "PI",
  "amount": "100.00",
  "callback_url": "https://client.app/webhook",
  "source_metadata": {},
  "target_metadata": {
    "pix_key": "user@example.com"
  }
}
```

**Response 201:**
```json
{
  "flow_id": "uuid",
  "status": "COMPLETED",
  "source": {...},
  "target": {...},
  "asset": "PI",
  "amount": "100.00",
  "result": {
    "target_reference": "PIX_TX_123"
  },
  "links": {
    "self": "/api/v1/bridge/flows/{flow_id}/",
    "events": "/api/v1/bridge/flows/{flow_id}/events/"
  }
}
```

### GET /api/v1/bridge/flows/{flow_id}/
Consulta um flow por ID.

### GET /api/v1/bridge/flows/{flow_id}/events/
Lista eventos de auditoria de um flow.

### POST /api/v1/bridge/flows/{flow_id}/cancel/
Cancela um flow (se ainda não completado).

### POST /api/v1/bridge/webhooks/test/
Endpoint de teste para receber webhooks e validar assinatura.

## 🔄 Estados do Fluxo

1. **INITIATED**: Flow criado
2. **VALIDATED**: Source e target validados
3. **BRIDGING**: Transferências em execução
4. **CONVERTED**: Conversão de moeda (opcional)
5. **COMPLETED**: Flow completado com sucesso
6. **FAILED**: Flow falhou
7. **CANCELED**: Flow cancelado

## 🔐 Segurança

### API Key
Configurar via variáveis de ambiente:
```bash
PPBRIDGE_API_KEY_ENABLED=true
PPBRIDGE_API_KEY=your_secret_key
```

### Webhook Signature
Webhooks são assinados com HMAC SHA-256:
```bash
PPBRIDGE_WEBHOOK_HMAC_SECRET=your_webhook_secret
```

Header: `X-PPBridge-Signature`

## 📊 Idempotência

Suporta idempotência via header `Idempotency-Key`:
- Mesma key + mesmo payload → retorna flow existente (200)
- Mesma key + payload diferente → 409 Conflict

## 🧪 Testes

```bash
cd backend
python manage.py test app.bridge.tests
```

## 📝 Variáveis de Ambiente

```bash
# API Security
PPBRIDGE_API_KEY_ENABLED=false  # true para habilitar
PPBRIDGE_API_KEY=change_me

# Webhooks
PPBRIDGE_WEBHOOK_HMAC_SECRET=change_me
PPBRIDGE_WEBHOOK_TIMEOUT_SECONDS=5
PPBRIDGE_WEBHOOK_MAX_RETRIES=3

# Logging
PPBRIDGE_LOG_LEVEL=INFO
```

## 🔗 Integração com PayPi-Bridge

O PPBridge Service está integrado ao projeto PayPi-Bridge existente:
- Usa o mesmo banco de dados PostgreSQL
- Compartilha configurações Django
- Disponível via `/api/v1/bridge/`
- Documentação OpenAPI em `/api/schema/swagger-ui/`

## 📚 Exemplos de Uso

### Criar Flow
```bash
curl -X POST http://localhost:8000/api/v1/bridge/flows/ \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "source": {"domain": "crypto", "adapter": "pi_network"},
    "target": {"domain": "finance", "adapter": "pix"},
    "asset": "PI",
    "amount": "100.00",
    "target_metadata": {"pix_key": "user@example.com"}
  }'
```

### Consultar Flow
```bash
curl http://localhost:8000/api/v1/bridge/flows/{flow_id}/
```

### Listar Eventos
```bash
curl http://localhost:8000/api/v1/bridge/flows/{flow_id}/events/
```

### Cancelar Flow
```bash
curl -X POST http://localhost:8000/api/v1/bridge/flows/{flow_id}/cancel/ \
  -H "Content-Type: application/json" \
  -d '{"reason": "User requested cancellation"}'
```

## 🎯 Próximos Passos

- [ ] Implementar adapters reais (Pi Network, Pix)
- [ ] Adicionar suporte a conversão de moeda (FX)
- [ ] Implementar processamento assíncrono (Celery)
- [ ] Adicionar métricas Prometheus
- [ ] Dashboard de monitoramento
