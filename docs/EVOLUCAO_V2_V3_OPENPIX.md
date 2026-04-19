# Evolução financeira: Versão 2, Versão 3 e Pix OpenPix

Este documento descreve as alterações de arquitetura e integração introduzidas no PayPi-Bridge: **multi-tenant com carteiras e ledger (V2)**, **partidas dobradas e resiliência (V3)** e **liquidação Pix via OpenPix** (alternativa ao mock Open Finance).

---

## 1. Visão geral

| Tema | O que foi adicionado |
|------|----------------------|
| **V2** | `Tenant`, `Wallet`, `LedgerEntry`, `FeeConfig`, `Settlement`; `PaymentIntent` com tenant e tipo; API de saldos; ledger simples + taxa; webhooks de tenant |
| **V3** | `LedgerAccount`, `JournalBatch`, `JournalLine` (double-entry); `RetryTask`; `IdempotencyRecord`; antifraude; comando de reconciliação; API v3; tarefa Celery de retry |
| **OpenPix** | Cliente HTTP `clients/openpix.py`; `SettlementPixPort` com `PIX_PROVIDER=openpix`; variáveis `OPENPIX_*` |

**Migrações Django:** `0005_tenant_wallet_ledger_v2`, `0006_v3_double_entry_retry_idempotency`.

---

## 2. Versão 2 — Multi-tenant, carteiras e ledger simples

### 2.1 Modelos (`app/paypibridge/models.py`)

- **`Tenant`**: cliente da API (`name`, `slug`, `api_key` único, `webhook_url`, `is_platform` para a conta interna que recebe taxas).
- **`Wallet`**: um registo por par `(tenant, asset)` com `asset` ∈ `PI` | `BRL`; saldo atualizado **apenas** pelos serviços de ledger (não editar saldo manualmente em produção).
- **`LedgerEntry`**: movimentos `credit` / `debit` por tenant, com `idempotency_key` opcional único (evita duplicar o mesmo evento).
- **`FeeConfig`**: percentagem sobre o **bruto em BRL** (ex.: `0.025` = 2,5%). Entrada ativa usada por `ledger_service.get_active_fee_rate()` com fallback em `SETTLEMENT_FEE_RATE`.
- **`Settlement`**: registo 1:1 com `PaymentIntent` após liquidação Pix concluída (auditoria).

**Extensões a `PaymentIntent`:** `tenant` (opcional), `source` (default `PI`), `external_pi_id`, `payment_type` (`one_time` | `subscription`).

### 2.2 Dados iniciais (migração `0005`)

- Tenant **plataforma** `slug=platform`, `api_key=ppb_platform_dev_key` (alterar em produção).
- `FeeConfig` default com taxa **0** (compatível com testes existentes).
- Wallets PI/BRL para o tenant plataforma.

### 2.3 Serviços

- **`services/ledger_service.py`**: `ensure_wallet`, `apply_ledger_entry` (transação + `select_for_update`), `credit_pi_for_verified_intent`, `apply_settlement_ledger`, cálculo de taxa.
- **`services/tenant_webhook.py`**: notificação HTTP best-effort para `tenant.webhook_url` (eventos de intent / liquidação).

### 2.4 Integração no fluxo

- **`POST /api/checkout/pi-intent`**: aceita `tenant_api_key` no body ou header **`X-PayPi-Tenant-Key`**; chave inválida → 401. Opcional: `payment_type`.
- **`POST /api/payments/verify`**: após verificação Pi bem-sucedida, grava `external_pi_id`, `status=CONFIRMED`, e em transação atómica credita PI no tenant (se existir).
- **`SettlementService`**: após Pix OK, cria/atualiza `Settlement`, aplica movimentos de ledger quando há tenant (e chama extensões V3 se ativas — ver secção 3).

### 2.5 API

| Método | Caminho | Descrição |
|--------|---------|-----------|
| GET | `/api/v2/tenant/wallets` | Saldos PI e BRL (header `X-PayPi-Tenant-Key`) |

### 2.6 Antifraude (partilhado com V3)

A partir desta evolução, o **`POST /api/checkout/pi-intent`** também passa por **`evaluate_intent_creation`** (valor máximo e limite de intents por hora por tenant). Ver secção 4.

---

## 3. Versão 3 — Double-entry, retry, idempotência

### 3.1 Modelos

- **`LedgerAccount`**: plano de contas (`code` único, `asset`, `account_type`, **`category`**: `ASSET` | `LIABILITY` | `REVENUE`), `balance`, ligação opcional 1:1 a `Wallet`.
- **`JournalBatch`**: cabeçalho de lançamento com `reference`, `idempotency_key` opcional, `payment_intent` opcional.
- **`JournalLine`**: linhas com `side` `debit` | `credit` e `amount` > 0; **soma de débitos = soma de créditos** por batch.
- **`RetryTask`**: fila persistente com `next_attempt` e backoff no processador.
- **`IdempotencyRecord`**: cache de resposta por `(scope, key)` para APIs idempotentes.

### 3.2 Migração `0006` (dados iniciais)

- Contas de sistema: `CLEARING_PI`, `CLEARING_BRL` (ativo), `PLATFORM_FEE_BRL` (receita).
- Para cada `Wallet` existente: conta `WALLET_T{id}_{asset}` (passivo) ligada ao `Wallet`.

### 3.3 Serviço double-entry

- **`services/double_entry_service.py`**: `post_balanced_journal`, `post_pi_received_journal`, `post_settlement_journals`, `reconcile_wallet_vs_account`, `is_double_entry_active()` (verifica existência de `CLEARING_PI`).

### 3.4 Comportamento em relação ao V2

- Em **`ledger_service`**, se **`is_double_entry_active()`** for verdadeiro, os fluxos de crédito PI e liquidação usam **journals balanceados** em vez das entradas simples `LedgerEntry`.
- Se a migração V3 não tiver corrido, mantém-se o ledger V2 apenas.

### 3.5 Retry e Celery

- Tarefa **`app.paypibridge.tasks.process_retry_tasks`**: processa `RetryTask` pendentes (handlers específicos podem ser acrescentados; tarefas sem handler podem ser marcadas como falha conforme implementação atual).
- **`config/settings.py`**: `CELERY_BEAT_SCHEDULE` inclui execução periódica de `process_retry_tasks` (intervalo configurado no settings).

### 3.6 Reconciliação

- Comando: `python manage.py reconcile_double_entry`
- Verifica alinhamento `Wallet` ↔ `LedgerAccount` e, para cada journal recente, sanidade débito/crédito.

### 3.7 API v3 (`app/paypibridge/views_v3.py`)

| Método | Caminho | Descrição |
|--------|---------|-----------|
| POST | `/api/v3/payments` | Cria intent (equivalente a checkout) + antifraude + header opcional **`Idempotency-Key`** |
| GET | `/api/v3/balance` | Saldos tenant (mesmo conceito que v2 wallets) |
| POST | `/api/v3/withdraw` | Reservado — devolve 501 |

### 3.8 Variáveis de ambiente (antifraude)

Definidas em `config/settings.py`:

- `FRAUD_MAX_PI_SINGLE` — valor Pi acima do qual se exige revisão manual (resposta 400 com código `manual_review`).
- `FRAUD_MAX_INTENTS_PER_HOUR` — limite de intents por tenant por hora (403 `fraud_blocked`).

---

## 4. OpenPix — Pix real (ou sandbox da Woovi)

### 4.1 Objetivo

Permitir que a liquidação **`SettlementPixPort`** chame a API **OpenPix** (`POST /api/v1/transfer`) em vez do mock ou do cliente Open Finance genérico, quando configurado.

### 4.2 Ficheiros

- **`app/paypibridge/clients/openpix.py`**: classe `OpenPixClient` — `transfer_to_pix_key` (valor em centavos, `fromPixKey` / `toPixKey`).
- **`app/paypibridge/services/settlement_pix_port.py`**: ordem de decisão:
  1. Se `PIX_PROVIDER=openpix` e faltam credenciais → erro `openpix_not_configured`.
  2. Se OpenPix está configurado → chamada à API.
  3. Senão, se mock OF → resposta sintética.
  4. Caso contrário → `PixClient` (Open Finance).

### 4.3 Variáveis de ambiente

Ver **`env.example`** (secção OpenPix). Resumo:

| Variável | Função |
|----------|--------|
| `PIX_PROVIDER` | Definir como `openpix` para ativar o cliente OpenPix |
| `OPENPIX_APP_ID` | AppID do painel API/Plugins (header `Authorization`) |
| `OPENPIX_FROM_PIX_KEY` | Chave Pix de **origem** (conta OpenPix) |
| `OPENPIX_BASE_URL` | Default `https://api.openpix.com.br/api/v1` |
| `OPENPIX_TIMEOUT` | Timeout HTTP em segundos |

A documentação pública da OpenPix usa **apenas o AppID** no `Authorization`; `OPENPIX_APP_SECRET` no `env.example` está reservado para usos futuros se a Woovi expuser OAuth ou outros fluxos.

### 4.4 Requisitos da API Woovi

- Transferências entre chaves podem exigir **permissão/BETA** na conta.
- O corpo inclui `value` (centavos), `fromPixKey`, `toPixKey`; a chave de destino é a enviada no fluxo de liquidação (`pix_key`).

### 4.5 Testes

- **`backend/tests/paypibridge/test_openpix.py`**: cobre sucesso com `requests` mockado e erro quando `PIX_PROVIDER=openpix` sem credenciais.

---

## 5. Migrações e deploy

1. Garantir dependências e `python manage.py migrate` até **`0006`** inclusive.
2. Em produção: **rodar chave da plataforma**, taxas em `FeeConfig`, e política **V2 vs V3** (usar apenas double-entry quando `CLEARING_PI` existir).
3. Para Pix OpenPix: preencher variáveis, validar `fromPixKey` no painel, testar primeiro em ambiente de homologação da Woovi.

---

## 6. Admin Django

Registos adicionais em **`app/paypibridge/admin.py`** para: `Tenant`, `Wallet`, `LedgerEntry`, `FeeConfig`, `Settlement`, modelos V3 (`LedgerAccount`, `JournalBatch`, `RetryTask`, `IdempotencyRecord`), etc.

---

## 7. Referências externas

- [OpenPix — Getting started API](https://developers.openpix.com.br/docs/apis/getting-started-api)
- [OpenPix — Transferir valores entre contas](https://developers.openpix.com.br/docs/transfer/how-to-transfer-values-between-accounts) (`/transfer`, valor em centavos)

---

*Documento alinhado ao estado do repositório após introdução das migrações 0005/0006, serviços de ledger/double-entry e integração OpenPix.*
