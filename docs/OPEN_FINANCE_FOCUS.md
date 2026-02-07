# Open Finance - Foco em Implementação

**Data**: 2026-02-07  
**Foco**: Consents, Link Bank Account, Payouts Pix, Reconcile

---

## 📋 Visão Geral

Este documento foca nos 4 componentes principais do Open Finance no PayPi-Bridge:

1. **Consents** - Gerenciamento de consentimentos
2. **Link Bank Account** - Vinculação de contas bancárias
3. **Payouts Pix** - Criação de pagamentos Pix
4. **Reconcile** - Reconciliação de transações

---

## 1️⃣ Consents

### Endpoints

- `POST /api/consents` - Criar consentimento
- `GET /api/consents` - Listar consentimentos do usuário
- `GET /api/consents/<id>` - Obter consentimento específico
- `POST /api/consents/<id>` - Atualizar/refresh consentimento

### Fluxo de Criação

```bash
POST /api/consents
Content-Type: application/json

{
  "provider": "banco_exemplo",
  "scopes": ["payments", "accounts"],
  "expiration_days": 90,
  "user_id": 1
}
```

**Response 201:**
```json
{
  "id": 1,
  "user": 1,
  "provider": "banco_exemplo",
  "scope": {"scopes": ["payments", "accounts"]},
  "consent_id": "consent_abc123",
  "status": "ACTIVE",
  "created_at": "2026-02-07T00:00:00Z",
  "expires_at": "2026-05-08T00:00:00Z"
}
```

### Implementação Atual

**Arquivos:**
- `backend/app/paypibridge/services/consent_service.py` - Lógica de negócio
- `backend/app/paypibridge/clients/open_finance.py` - Cliente Open Finance
- `backend/app/paypibridge/views.py` - `ConsentView`, `ConsentDetailView`

**Funcionalidades:**
- ✅ Criação de consent via API Open Finance
- ✅ Validação de consent (status, expiração)
- ✅ Refresh de consent (atualizar dados do servidor)
- ✅ Busca de consent ativo por usuário/provedor
- ✅ Suporte a mock mode (`OF_USE_MOCK=true`)

**Melhorias Necessárias:**
- [ ] Tratamento de erros mais robusto
- [ ] Logging estruturado melhorado
- [ ] Validação de scopes antes de criar
- [ ] Cache de tokens OAuth2
- [ ] Retry automático em caso de falha

---

## 2️⃣ Link Bank Account

### Endpoint

- `POST /api/bank-accounts/link` - Vincular conta bancária a um consent

### Fluxo

```bash
POST /api/bank-accounts/link
Content-Type: application/json

{
  "consent_id": 1,
  "institution": "Banco Exemplo",
  "account_id": "account_123",
  "branch": "0001",
  "number": "12345-6",
  "ispb": "12345678",
  "user_id": 1
}
```

**Response 201:**
```json
{
  "id": 1,
  "user": 1,
  "consent": 1,
  "institution": "Banco Exemplo",
  "account_id": "account_123",
  "branch": "0001",
  "number": "12345-6",
  "ispb": "12345678"
}
```

### Implementação Atual

**Arquivos:**
- `backend/app/paypibridge/services/consent_service.py` - `link_bank_account()`
- `backend/app/paypibridge/clients/open_finance.py` - `get_accounts()`
- `backend/app/paypibridge/views.py` - `LinkBankAccountView`

**Funcionalidades:**
- ✅ Busca de contas via Open Finance API
- ✅ Validação de conta existe na lista retornada
- ✅ Criação de registro `BankAccount` no banco
- ✅ Fallback: cria mesmo se não encontrar na lista

**Melhorias Necessárias:**
- [ ] Validação mais rigorosa de contas
- [ ] Suporte a múltiplas contas por consent
- [ ] Endpoint para listar contas vinculadas
- [ ] Endpoint para desvincular conta
- [ ] Validação de ISPB e formato de conta

---

## 3️⃣ Payouts Pix

### Endpoint

- `POST /api/payouts/pix` - Criar pagamento Pix

### Fluxo

```bash
POST /api/payouts/pix
Content-Type: application/json

{
  "payee_user_id": 1,
  "amount_brl": "100.00",
  "cpf": "12345678901",
  "pix_key": "user@example.com",
  "description": "Pagamento via PayPi-Bridge"
}
```

**Response 201:**
```json
{
  "txid": "E20260207123456789012345678901234",
  "status": "SETTLED",
  "amount": "100.00",
  "currency": "BRL",
  "created_at": "2026-02-07T00:00:00Z",
  "paymentId": "E20260207123456789012345678901234"
}
```

### Implementação Atual

**Arquivos:**
- `backend/app/paypibridge/clients/pix.py` - `PixClient`
- `backend/app/paypibridge/clients/open_finance.py` - `create_pix_payment()`
- `backend/app/paypibridge/views.py` - `PixPayoutView`

**Funcionalidades:**
- ✅ Criação de pagamento Pix imediato
- ✅ Validação de consent ativo
- ✅ Geração automática de E2E ID
- ✅ Suporte a mock mode
- ✅ Tratamento de erros HTTP

**Melhorias Necessárias:**
- [ ] Endpoint para consultar status do pagamento
- [ ] Webhook para notificações de status
- [ ] Retry automático em caso de falha
- [ ] Validação de formato de chave Pix
- [ ] Suporte a pagamentos agendados
- [ ] Rate limiting específico
- [ ] Idempotência via Idempotency-Key

---

## 4️⃣ Reconcile

### Endpoint

- `POST /api/reconcile` - Reconciliação de pagamento

### Fluxo

```bash
POST /api/reconcile
Content-Type: application/json

{
  "consent_id": 1,
  "account_id": "account_123",
  "expected_amount": "100.00",
  "expected_txid": "E20260207123456789012345678901234",
  "user_id": 1
}
```

**Response 200:**
```json
{
  "found": true,
  "transaction": {
    "transactionId": "E20260207123456789012345678901234",
    "amount": "100.00",
    "status": "SETTLED",
    "date": "2026-02-07T00:00:00Z"
  },
  "matched_by": "amount_and_txid"
}
```

### Implementação Atual

**Arquivos:**
- `backend/app/paypibridge/clients/open_finance.py` - `reconcile_payment()`
- `backend/app/paypibridge/views.py` - `ReconcilePaymentView`

**Funcionalidades:**
- ✅ Busca de transações da conta
- ✅ Matching por valor e/ou txid
- ✅ Retorno de transação encontrada

**Melhorias Necessárias:**
- [ ] Matching mais inteligente (tolerância de valor)
- [ ] Busca em múltiplas contas
- [ ] Cache de transações recentes
- [ ] Suporte a reconciliação automática periódica
- [ ] Logging detalhado de matching
- [ ] Endpoint para histórico de reconciliações

---

## 🔄 Fluxo Completo Integrado

### 1. Criar Consent

```bash
curl -X POST https://api.example.com/api/consents \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "banco_exemplo",
    "scopes": ["payments", "accounts"],
    "expiration_days": 90,
    "user_id": 1
  }'
```

### 2. Vincular Conta Bancária

```bash
curl -X POST https://api.example.com/api/bank-accounts/link \
  -H "Content-Type: application/json" \
  -d '{
    "consent_id": 1,
    "institution": "Banco Exemplo",
    "account_id": "account_123",
    "branch": "0001",
    "number": "12345-6",
    "ispb": "12345678",
    "user_id": 1
  }'
```

### 3. Criar Pagamento Pix

```bash
curl -X POST https://api.example.com/api/payouts/pix \
  -H "Content-Type: application/json" \
  -d '{
    "payee_user_id": 1,
    "amount_brl": "100.00",
    "cpf": "12345678901",
    "pix_key": "user@example.com",
    "description": "Pagamento via PayPi-Bridge"
  }'
```

### 4. Reconciliação

```bash
curl -X POST https://api.example.com/api/reconcile \
  -H "Content-Type: application/json" \
  -d '{
    "consent_id": 1,
    "account_id": "account_123",
    "expected_amount": "100.00",
    "expected_txid": "E20260207123456789012345678901234",
    "user_id": 1
  }'
```

---

## 🛠️ Melhorias Prioritárias

### Fase 1 - Estabilidade e Robustez

1. **Tratamento de Erros**
   - Padronizar respostas de erro
   - Códigos de erro específicos
   - Mensagens claras para o usuário

2. **Logging**
   - Logs estruturados em todos os endpoints
   - Correlation IDs
   - Métricas de performance

3. **Validações**
   - Validação de formato de chave Pix
   - Validação de CPF
   - Validação de valores monetários

### Fase 2 - Funcionalidades Adicionais

1. **Status de Pagamento**
   - Endpoint `GET /api/payouts/pix/<txid>/status`
   - Webhook para mudanças de status
   - Polling automático

2. **Listagem**
   - `GET /api/bank-accounts` - Listar contas vinculadas
   - `GET /api/payouts/pix` - Listar pagamentos Pix
   - Paginação e filtros

3. **Idempotência**
   - Suporte a `Idempotency-Key` em Payouts
   - Prevenção de duplicatas

### Fase 3 - Otimizações

1. **Cache**
   - Cache de tokens OAuth2
   - Cache de contas bancárias
   - Cache de transações recentes

2. **Retry e Circuit Breaker**
   - Retry automático em falhas temporárias
   - Circuit breaker já implementado, melhorar configuração

3. **Reconciliação Automática**
   - Task periódica para reconciliar pagamentos pendentes
   - Notificações de reconciliação bem-sucedida

---

## 📊 Status Atual

| Componente | Status | Funcionalidades | Melhorias Necessárias |
|------------|--------|-----------------|----------------------|
| **Consents** | ✅ Funcional | Criação, Listagem, Refresh, Validação | Tratamento de erros, Cache de tokens |
| **Link Bank Account** | ✅ Funcional | Vinculação, Validação básica | Listagem, Desvinculação, Validação rigorosa |
| **Payouts Pix** | ✅ Funcional | Criação, Mock mode | Status, Webhook, Idempotência |
| **Reconcile** | ✅ Funcional | Matching básico | Matching inteligente, Cache, Automatização |

---

## 🧪 Testes

### Testes Necessários

1. **Consents**
   - Teste de criação bem-sucedida
   - Teste de criação com mock
   - Teste de validação de consent expirado
   - Teste de refresh de consent

2. **Link Bank Account**
   - Teste de vinculação bem-sucedida
   - Teste de validação de conta existente
   - Teste de fallback quando conta não encontrada

3. **Payouts Pix**
   - Teste de criação bem-sucedida
   - Teste de criação com mock
   - Teste de validação de consent ativo
   - Teste de tratamento de erros

4. **Reconcile**
   - Teste de reconciliação bem-sucedida
   - Teste de matching por valor
   - Teste de matching por txid
   - Teste quando transação não encontrada

---

## 📝 Próximos Passos

1. ✅ Documentar estado atual
2. ⏳ Implementar melhorias de tratamento de erros
3. ⏳ Adicionar endpoints de status e listagem
4. ⏳ Implementar testes completos
5. ⏳ Adicionar idempotência em Payouts
6. ⏳ Implementar webhooks para status de pagamento
7. ⏳ Adicionar reconciliação automática

---

**Última atualização**: 2026-02-07
