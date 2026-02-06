# Open Finance Integration - PayPi-Bridge

## 📋 Visão Geral

A integração com Open Finance (Open Banking Brasil) permite que o PayPi-Bridge:

### Modo Mock (desenvolvimento / sandbox sem provedor)

Se `OF_BASE_URL` estiver vazio **ou** `OF_USE_MOCK=true` no `.env`, o backend usa **mock**:
- **POST /api/consents** cria um consent no banco com `consent_id` no formato `mock_consent_xxx` (sem chamar API externa).
- **POST /api/payouts/pix** retorna `txid` e `status: SETTLED` simulados (sem enviar Pix real).
- **GET /api/consents**, **link bank account** e **reconcile** também funcionam em mock.

Use `user_id=1` (ou outro id de usuário de teste) no body/query; autenticação será implementada depois. Ver `.env.example` para variáveis `OF_*`.

---

A integração real permite que o PayPi-Bridge:
- Crie pagamentos Pix via Payments Initiation API
- Acesse informações de contas bancárias
- Reconcilie transações automaticamente
- Gerencie consentimentos de usuários

## 🔐 Autenticação

### mTLS (Mutual TLS)

O Open Finance requer autenticação via mTLS usando certificados cliente:

```python
# Configurar no .env
OF_MTLS_CERT_PATH=/path/to/client.crt
OF_MTLS_KEY_PATH=/path/to/client.key
OF_CA_CERT_PATH=/path/to/ca.crt
```

### OAuth2

Após autenticação mTLS, é necessário obter access token OAuth2:

```python
from app.paypibridge.clients.open_finance import OpenFinanceClient

client = OpenFinanceClient.from_env()
token = client._get_access_token(consent_id="consent_123")
```

## 📝 Consent Management

### Criar Consentimento

```python
from app.paypibridge.services.consent_service import get_consent_service

service = get_consent_service()

consent = service.create_consent(
    user=request.user,
    provider="banco_exemplo",
    scopes=["payments", "accounts"],
    expiration_days=90
)
```

### Validar Consentimento

```python
is_valid = service.validate_consent(consent)
if is_valid:
    # Consentimento ativo e válido
    pass
```

### Obter Consentimento Ativo

```python
active_consent = service.get_active_consent(
    user=request.user,
    provider="banco_exemplo"  # opcional
)
```

## 💰 Payments Initiation API (Pix)

### Criar Pagamento Pix

```python
from app.paypibridge.clients.pix import PixClient
from app.paypibridge.models import Consent

consent = Consent.objects.get(id=consent_id)
pix_client = PixClient.from_env(consent=consent)

result = pix_client.create_immediate_payment(
    cpf="12345678901",
    pix_key="test@example.com",
    amount_brl="100.00",
    description="Pagamento via PayPi-Bridge"
)

# Resultado:
# {
#     "txid": "E2E123456789",
#     "status": "PENDING",
#     "amount": "100.00",
#     "currency": "BRL"
# }
```

### Verificar Status do Pagamento

```python
status = pix_client.get_payment_status(payment_id="E2E123456789")
```

## 🏦 Accounts API

### Listar Contas

```python
from app.paypibridge.clients.open_finance import OpenFinanceClient

client = OpenFinanceClient.from_env()
accounts = client.get_accounts(consent_id="consent_123")
```

### Obter Transações

```python
from datetime import datetime, timedelta

from_date = datetime.now() - timedelta(days=7)
transactions = client.get_account_transactions(
    consent_id="consent_123",
    account_id="account_456",
    from_date=from_date
)
```

## 🔄 Reconciliação

### Reconciliação Automática

```python
result = client.reconcile_payment(
    consent_id="consent_123",
    account_id="account_456",
    expected_amount="100.00",
    expected_txid="E2E123456789"  # opcional
)

# Resultado:
# {
#     "found": True,
#     "transaction": {...},
#     "matched_by": "amount_and_txid"
# }
```

## 🔗 API Endpoints

### Consent Management

- `POST /api/consents` - Criar consentimento
- `GET /api/consents` - Listar consentimentos do usuário
- `GET /api/consents/<id>` - Obter consentimento específico
- `POST /api/consents/<id>` - Atualizar consentimento

### Bank Accounts

- `POST /api/bank-accounts/link` - Vincular conta bancária

### Reconciliation

- `POST /api/reconcile` - Reconciliação de pagamento

## 📊 Fluxo Completo

### 1. Criar Consentimento

```bash
POST /api/consents
{
    "provider": "banco_exemplo",
    "scopes": ["payments", "accounts"],
    "expiration_days": 90
}
```

### 2. Vincular Conta Bancária

```bash
POST /api/bank-accounts/link
{
    "consent_id": 1,
    "institution": "Banco Exemplo",
    "account_id": "account_123",
    "branch": "0001",
    "number": "12345-6",
    "ispb": "12345678"
}
```

### 3. Criar Pagamento Pix

```bash
POST /api/payouts/pix
{
    "payee_user_id": 1,
    "amount_brl": "100.00",
    "cpf": "12345678901",
    "pix_key": "test@example.com",
    "description": "Pagamento via PayPi-Bridge"
}
```

### 4. Reconciliação

```bash
POST /api/reconcile
{
    "consent_id": 1,
    "account_id": "account_123",
    "expected_amount": "100.00",
    "expected_txid": "E2E123456789"
}
```

## ⚠️ Tratamento de Erros

### Erros Comuns

1. **Consentimento Expirado**
   - Status: `EXPIRED`
   - Solução: Criar novo consentimento

2. **Token OAuth2 Inválido**
   - Erro: `401 Unauthorized`
   - Solução: Token é renovado automaticamente

3. **mTLS Inválido**
   - Erro: `SSL/TLS error`
   - Solução: Verificar certificados no .env

4. **Pagamento Rejeitado**
   - Status: `REJECTED`
   - Solução: Verificar dados do pagamento

## 🔒 Segurança

### Certificados

- Certificados devem ser armazenados de forma segura
- Não commitar certificados no repositório
- Usar variáveis de ambiente ou secret management

### Tokens

- Tokens OAuth2 são cacheados e renovados automaticamente
- Tokens expiram após 1 hora (padrão)
- Renovação automática 5 minutos antes da expiração

### Consents

- Consents são vinculados a usuários específicos
- Validação de ownership em todas as operações
- Expiração automática após data limite

## 📚 Referências

- [Open Banking Brasil](https://www.bcb.gov.br/estabilidadefinanceira/openbanking)
- [Payments Initiation API](https://openbanking-brasil.github.io/specs-seguranca/open-banking-brasil-payments-api-1_ID2.html)
- [Accounts API](https://openbanking-brasil.github.io/specs-seguranca/open-banking-brasil-accounts-api-1_ID2.html)

---

**Última atualização**: 2025-01-30
