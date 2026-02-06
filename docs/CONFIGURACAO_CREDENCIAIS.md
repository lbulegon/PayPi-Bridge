# Configuração de Credenciais Reais - PayPi-Bridge

**Data**: 2026-02-06  
**Fase**: 2 - Integrações Reais

---

## 📋 VISÃO GERAL

Este documento descreve como configurar credenciais reais para todas as integrações do PayPi-Bridge:
- Pi Network
- Open Finance / Open Banking
- Soroban / Stellar
- Taxa de Câmbio (FX)

---

## 🔑 PI NETWORK

### Obter Credenciais

1. **Acesse o Pi Developer Portal**
   - URL: https://developers.minepi.com/
   - Ou portal oficial atual da Pi Network

2. **Criar/Configurar Aplicação**
   - Crie uma nova aplicação ou use existente
   - Anote a **API Key** da aplicação
   - Gere ou use uma **Wallet Seed** (começa com `S`, 56 caracteres)

3. **Escolher Ambiente**
   - **Pi Testnet**: Para desenvolvimento e testes
   - **Pi Network**: Para produção (mainnet)

### Configurar Variáveis de Ambiente

Adicione ao `.env`:

```bash
# Pi Network
PI_API_KEY=sua_api_key_aqui
PI_WALLET_PRIVATE_SEED=S...sua_seed_56_caracteres_aqui
PI_NETWORK=Pi Testnet  # ou "Pi Network" para produção
```

### Verificar Configuração

```bash
# Testar via API
curl http://localhost:9080/api/pi/status

# Deve retornar:
# {
#   "configured": true,
#   "network": "Pi Testnet",
#   "message": "Pi Network configurado..."
# }
```

### Testar Saldo

```bash
curl http://localhost:9080/api/pi/balance

# Deve retornar saldo em Pi
```

---

## 🏦 OPEN FINANCE / OPEN BANKING

### Obter Credenciais

1. **Registrar no Diretório de Participantes**
   - Acesse: https://www.bcb.gov.br/estabilidadefinanceira/openbanking
   - Registre sua organização como Participante

2. **Obter Certificados mTLS**
   - Certificado cliente (`.crt`)
   - Chave privada (`.key`)
   - Certificado CA (opcional, `.crt`)

3. **Obter Credenciais OAuth2**
   - `CLIENT_ID`: ID do cliente OAuth2
   - `CLIENT_SECRET`: Secret do cliente OAuth2

4. **Escolher Provedor (ASPSP)**
   - Banco do Brasil
   - Itaú
   - Bradesco
   - Outros participantes do Open Banking

### Configurar Variáveis de Ambiente

Adicione ao `.env`:

```bash
# Open Finance / Open Banking
OF_BASE_URL=https://api.openbanking.banco.com.br  # URL do provedor
OF_CLIENT_ID=seu_client_id_oauth2
OF_CLIENT_SECRET=seu_client_secret_oauth2
OF_MTLS_CERT_PATH=/path/to/client.crt
OF_MTLS_KEY_PATH=/path/to/client.key
OF_CA_CERT_PATH=/path/to/ca.crt  # Opcional
OF_ORG_ID=seu_organisational_id
OF_USE_MOCK=false  # true para usar mock em desenvolvimento
```

### Configurar Certificados

1. **Colocar certificados em local seguro**
   ```bash
   mkdir -p /secure/certs
   cp client.crt /secure/certs/
   cp client.key /secure/certs/
   cp ca.crt /secure/certs/  # Se disponível
   chmod 600 /secure/certs/*.key
   ```

2. **Atualizar paths no .env**
   ```bash
   OF_MTLS_CERT_PATH=/secure/certs/client.crt
   OF_MTLS_KEY_PATH=/secure/certs/client.key
   OF_CA_CERT_PATH=/secure/certs/ca.crt
   ```

### Testar Integração

```bash
# Criar consentimento
curl -X POST http://localhost:9080/api/consents \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "banco_exemplo",
    "scopes": ["payments", "accounts"],
    "expiration_days": 90
  }'
```

---

## ⛓️ SOROBAN / STELLAR

### Configurar Soroban

1. **Escolher Rede**
   - **Testnet**: `https://soroban-testnet.stellar.org`
   - **Mainnet**: `https://soroban-mainnet.stellar.org` (quando disponível)

2. **Deploy do Contrato**
   - Deploy do contrato `paypi_bridge.rs` no Soroban
   - Anotar o **Contract ID**

### Configurar Variáveis de Ambiente

Adicione ao `.env`:

```bash
# Soroban / Stellar
SOROBAN_RPC_URL=https://soroban-testnet.stellar.org
SOROBAN_CONTRACT_ID=seu_contract_id_aqui
RELAYER_WEBHOOK_URL=http://localhost:9080/api/webhooks/ccip
RELAYER_POLL_INTERVAL=30  # segundos entre polls
```

### Monitorar Eventos

O relayer monitora automaticamente eventos do contrato quando configurado.

---

## 💱 TAXA DE CÂMBIO (FX)

### Opções de Provedor

#### Opção 1: Taxa Fixa (Desenvolvimento)
```bash
FX_PROVIDER=fixed
FX_FIXED_RATE=4.76  # Taxa fixa Pi → BRL
```

#### Opção 2: API Externa
```bash
FX_PROVIDER=api
FX_API_URL=https://api.exchangerate.com/v1/convert
FX_API_KEY=sua_api_key
FX_CACHE_TIMEOUT=300  # segundos (5 minutos)
```

#### Opção 3: Custom (Implementar)
```bash
FX_PROVIDER=custom
# Implementar método _fetch_custom() em fx_service.py
```

### Configurar Variáveis de Ambiente

Adicione ao `.env`:

```bash
# Taxa de Câmbio
FX_PROVIDER=fixed  # fixed, api, ou custom
FX_FIXED_RATE=4.76
FX_API_URL=  # Se usar provider=api
FX_API_KEY=  # Se usar provider=api
FX_CACHE_TIMEOUT=300
```

---

## 🔄 CELERY (Tarefas Assíncronas)

### Configurar Redis

O Celery precisa de Redis como broker e result backend.

```bash
# Redis já configurado no docker-compose.yml
# Ou configure manualmente:
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Iniciar Workers

```bash
# Worker principal
cd backend
celery -A config worker --loglevel=info

# Beat scheduler (para tarefas periódicas)
celery -A config beat --loglevel=info
```

### Tarefas Configuradas

- `monitor-soroban-events`: A cada 30 segundos
- `process-incomplete-payments`: A cada 5 minutos
- `update-fx-rates`: A cada 5 minutos

---

## 🔐 SEGURANÇA

### Webhook Secret

```bash
# Gerar secret seguro para webhooks CCIP
CCIP_WEBHOOK_SECRET=$(openssl rand -hex 32)
```

### Django Secret Key

```bash
# Gerar secret key seguro para Django
DJANGO_SECRET_KEY=$(openssl rand -hex 32)
```

### Allowlist de IPs (Opcional)

```bash
CCIP_RELAYER_WHITELIST=1.2.3.4,5.6.7.8
```

---

## 📝 CHECKLIST DE CONFIGURAÇÃO

### Pi Network
- [ ] API Key obtida do Developer Portal
- [ ] Wallet Seed gerada/configurada
- [ ] Ambiente escolhido (Testnet/Mainnet)
- [ ] Variáveis configuradas no `.env`
- [ ] Testado `/api/pi/status` e `/api/pi/balance`

### Open Finance
- [ ] Organização registrada no Diretório
- [ ] Certificados mTLS obtidos
- [ ] Credenciais OAuth2 configuradas
- [ ] Provedor escolhido (banco)
- [ ] Certificados colocados em local seguro
- [ ] Variáveis configuradas no `.env`
- [ ] Testado criação de consentimento

### Soroban
- [ ] Contrato deployado
- [ ] Contract ID anotado
- [ ] RPC URL configurada
- [ ] Variáveis configuradas no `.env`
- [ ] Relayer testado (se aplicável)

### Taxa de Câmbio
- [ ] Provedor escolhido (fixed/api/custom)
- [ ] Credenciais configuradas (se API)
- [ ] Variáveis configuradas no `.env`
- [ ] Testado conversão Pi → BRL

### Celery
- [ ] Redis configurado e rodando
- [ ] Workers iniciados
- [ ] Beat scheduler iniciado
- [ ] Tarefas periódicas funcionando

---

## 🧪 TESTES

### Testar Pi Network

```bash
# Status
curl http://localhost:9080/api/pi/status

# Saldo
curl http://localhost:9080/api/pi/balance

# Verificar pagamento
curl -X POST http://localhost:9080/api/payments/verify \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": "payment_123",
    "intent_id": "pi_1234567890"
  }'
```

### Testar Open Finance

```bash
# Criar consentimento
curl -X POST http://localhost:9080/api/consents \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "banco_exemplo",
    "scopes": ["payments"],
    "expiration_days": 90
  }'

# Criar Pix payout
curl -X POST http://localhost:9080/api/payouts/pix \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "payee_user_id": 1,
    "amount_brl": "100.00",
    "cpf": "12345678901",
    "pix_key": "test@example.com"
  }'
```

### Testar Webhook CCIP

```bash
# Gerar HMAC signature
SECRET="seu-secret"
BODY='{"intent_id":"pi_123","fx_quote":{"brl_amount":"50.00"},"status":"CONFIRMED"}'
SIG=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | cut -d' ' -f2)

# Enviar webhook
curl -X POST http://localhost:9080/api/webhooks/ccip \
  -H "Content-Type: application/json" \
  -H "X-Signature: $SIG" \
  -d "$BODY"
```

---

## 🚨 TROUBLESHOOTING

### Pi Network não disponível

**Problema**: `GET /api/pi/status` retorna `configured: false`

**Soluções**:
1. Verificar se `PI_API_KEY` e `PI_WALLET_PRIVATE_SEED` estão no `.env`
2. Verificar se backend foi reiniciado após alterar `.env`
3. Verificar formato da seed (deve começar com `S` e ter 56 caracteres)
4. Verificar se `PI_NETWORK` está correto (`Pi Testnet` ou `Pi Network`)

### Open Finance mTLS falha

**Problema**: Erro ao conectar com APIs Open Finance

**Soluções**:
1. Verificar paths dos certificados no `.env`
2. Verificar permissões dos arquivos (chmod 600 para `.key`)
3. Verificar se certificados não expiraram
4. Verificar se CA cert está correto

### Circuit Breaker aberto

**Problema**: Requests bloqueados por circuit breaker

**Soluções**:
1. Verificar logs para identificar falhas
2. Aguardar timeout de recuperação (60s por padrão)
3. Resetar manualmente se necessário:
   ```python
   from app.paypibridge.clients.open_finance import OpenFinanceClient
   client = OpenFinanceClient.from_env()
   client._circuit_breaker.reset()
   ```

### Celery não processa tarefas

**Problema**: Tarefas ficam pendentes

**Soluções**:
1. Verificar se Redis está rodando
2. Verificar `CELERY_BROKER_URL` e `CELERY_RESULT_BACKEND`
3. Verificar logs do worker: `celery -A config worker --loglevel=debug`
4. Verificar se tasks estão sendo descobertas: `celery -A config inspect registered`

---

## 📚 RECURSOS E LINKS

### Pi Network
- Developer Portal: https://developers.minepi.com/
- Documentação: https://developers.minepi.com/docs

### Open Banking Brasil
- Diretório: https://www.bcb.gov.br/estabilidadefinanceira/openbanking
- Especificações: https://openbankingbrasil.org.br/

### Soroban
- Documentação: https://soroban.stellar.org/docs
- RPC Testnet: https://soroban-testnet.stellar.org

### Stellar
- Documentação: https://developers.stellar.org/
- Network: https://developers.stellar.org/docs/encyclopedia/networks

---

**Última atualização**: 2026-02-06  
**Próxima revisão**: Após testes com credenciais reais
