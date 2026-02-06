# Webhook CCIP – PayPi-Bridge

Endpoint para receber eventos do relayer (ex.: Soroban) e atualizar o PaymentIntent (fx_quote, amount_brl, status). Inclui validação HMAC e idempotência.

---

## Endpoint

- **URL:** `POST /api/webhooks/ccip`
- **Header obrigatório:** `X-Signature` = HMAC-SHA256 do **corpo bruto** (body) da requisição, em hexadecimal, usando `CCIP_WEBHOOK_SECRET` como chave.
- **Content-Type:** `application/json`

---

## Formato do payload (JSON)

| Campo      | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `intent_id` | Sim       | ID do PaymentIntent a atualizar (ex.: `pi_1234567890`) |
| `event_id`  | Não (recomendado) | ID único do evento. Se enviado, o mesmo evento não é processado duas vezes (idempotência). |
| `fx_quote`   | Não       | Objeto com cotação FX. Ex.: `{"brl_amount": "50.00", "rate": "0.15"}` |
| `status`    | Não       | Novo status do intent: `CONFIRMED`, `SETTLED` ou `CANCELLED`. Default: `CONFIRMED` |

### Exemplo mínimo

```json
{
  "intent_id": "pi_1734567890123",
  "event_id": "evt_soroban_abc123",
  "fx_quote": {
    "brl_amount": "50.00",
    "rate": "0.15"
  },
  "status": "CONFIRMED"
}
```

### Exemplo sem idempotência (sem `event_id`)

```json
{
  "intent_id": "pi_1734567890123",
  "fx_quote": { "brl_amount": "50.00" }
}
```

Sem `event_id`, cada POST será processado (sem garantia de idempotência).

---

## Validação HMAC

1. O relayer usa o **corpo bruto** da requisição (bytes do JSON, sem alterar espaços/capitalização).
2. Calcula `HMAC-SHA256(body, CCIP_WEBHOOK_SECRET)` e converte o resultado para **hexadecimal** (string em minúsculas).
3. Envia no header: `X-Signature: <hex>`.

### Exemplo em Python (gerar assinatura para testes)

```python
import hmac
import hashlib
import json

secret = "replace-with-random-hmac"  # mesmo valor de CCIP_WEBHOOK_SECRET no .env
payload = {
    "intent_id": "pi_1734567890123",
    "event_id": "evt_test_001",
    "fx_quote": {"brl_amount": "50.00"},
    "status": "CONFIRMED",
}
body = json.dumps(payload, separators=(",", ":"))  # corpo exato que será enviado
signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
print("X-Signature:", signature)
print("Body:", body)
```

### Exemplo com curl

Use o script abaixo para gerar a assinatura e depois:

```bash
curl -X POST http://localhost:9080/api/webhooks/ccip \
  -H "Content-Type: application/json" \
  -H "X-Signature: <valor_gerado_pelo_script>" \
  -d '{"intent_id":"pi_123","event_id":"evt_1","fx_quote":{"brl_amount":"50.00"},"status":"CONFIRMED"}'
```

---

## Respostas

| Código | Situação |
|--------|----------|
| 200 | Evento processado com sucesso ou já processado (idempotência). Corpo: `{"ok": true}` ou `{"ok": true, "already_processed": true}` |
| 400 | Payload inválido (ex.: falta `intent_id`) |
| 403 | Assinatura HMAC inválida |
| 404 | PaymentIntent não encontrado |
| 503 | `CCIP_WEBHOOK_SECRET` não configurado no servidor |

---

## Idempotência

- Se o payload incluir `event_id`, o backend verifica se já existe um `WebhookEvent` com o mesmo `intent_id` + `event_id`.
- Se existir, responde **200** com `"already_processed": true` e **não** altera o intent novamente.
- Se não existir, processa o evento, atualiza o intent e grava o `WebhookEvent`.

Recomenda-se sempre enviar `event_id` (ex.: ID do evento on-chain ou UUID gerado pelo relayer).

---

## Payout Pix após webhook

O webhook apenas **atualiza** o PaymentIntent (fx_quote, amount_brl, status). Não dispara Pix automaticamente.

Para enviar o Pix após confirmação:

1. O relayer (ou outro serviço) pode chamar **POST /api/payouts/pix** após receber confirmação on-chain, usando o mesmo `payee_user_id` e dados do intent.
2. Ou implementar um job/cron que lista intents com status `CONFIRMED` e dispara o payout conforme regra de negócio.

Variáveis de ambiente: ver `.env.example` (`CCIP_WEBHOOK_SECRET`).
