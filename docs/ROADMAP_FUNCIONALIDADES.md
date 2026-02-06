# Roteiro de implementação – PayPi-Bridge

Ordem sugerida para implementar as funcionalidades passo a passo.

---

## Por onde começar

**Ordem recomendada:** Fundação (checkout + Pi) → depois Open Finance → depois Webhook/Relayer.

---

## Passo 1 – Fundação (checkout + Pi) — **começar aqui**

**Objetivo:** Fluxo mínimo funcionando: criar PaymentIntent e consultar saldo Pi (ou resposta clara quando Pi não estiver configurado).

### 1.1 Ter um usuário no banco

- O endpoint `POST /api/checkout/pi-intent` exige `payee_user_id` (FK para `User`).
- Criar um usuário de teste (ex.: superusuário ou usuário fixo para desenvolvimento).

**No servidor:**
```bash
docker compose exec backend python manage.py createsuperuser
# ou criar um usuário de teste via shell/script
```

### 1.2 Testar criar PaymentIntent

- **POST** `/api/checkout/pi-intent`  
  Body exemplo: `{"payee_user_id": 1, "amount_pi": "10.5", "metadata": {}}`
- Verificar se retorna 201 e o `intent_id` no JSON.

### 1.3 Testar GET /api/pi/balance

- **GET** `/api/pi/balance`
- **Com Pi configurado** (`.env`: `PI_API_KEY`, `PI_WALLET_PRIVATE_SEED`): deve retornar saldo.
- **Sem Pi configurado**: deve retornar 503 com mensagem clara (já está assim no código).

### 1.4 (Opcional) Modo mock para desenvolvimento

- Se não tiver credenciais Pi ainda: endpoint de “simular” pagamento ou flag para aceitar um `payment_id` de teste em `POST /api/payments/verify`.

**Resumo Passo 1:** usuário no banco → criar intent → testar pi/balance (e, se quiser, verify com mock).

---

## Passo 2 – Verificação de pagamento Pi

**Objetivo:** Vincular um pagamento Pi a um PaymentIntent.

- Configurar Pi no `.env` (API key + wallet seed).
- **POST** `/api/payments/verify` com `payment_id` e `intent_id`.
- Garantir que o intent seja atualizado (payer_address, metadata com pi_payment_id, etc.) e que a resposta reflita isso.

---

## Passo 3 – Open Finance (Consents, Pix, Reconcile)

**Objetivo:** Consents e Pix payout funcionando (sandbox ou produção).

- Depende de credenciais Open Finance (mTLS, OAuth2, etc.).
- Endpoints já existem: `/api/consents`, `/api/payouts/pix`, `/api/reconcile`, etc.
- Foco: validar fluxo com um provedor (sandbox) e ajustar clients/serializers se necessário.

---

## Passo 4 – Webhook CCIP e Relayer

**Objetivo:** Receber eventos (ex.: Soroban) e processar via `/api/webhooks/ccip`.

- Validar HMAC e payload.
- Atualizar PaymentIntent e, se aplicável, disparar payout Pix (integrando com Passo 3).

---

## Resumo visual

| Passo | Foco                    | Endpoints principais                          |
|-------|-------------------------|-----------------------------------------------|
| **1** | Fundação (checkout + Pi) | `POST /api/checkout/pi-intent`, `GET /api/pi/balance` |
| **2** | Verificar pagamento Pi  | `POST /api/payments/verify`                  |
| **3** | Open Finance            | Consents, Pix, Reconcile                      |
| **4** | Webhook / Relayer        | `POST /api/webhooks/ccip`                     |

**Começar pelo Passo 1:** usuário no banco + testar criar intent + testar `/api/pi/balance`.
