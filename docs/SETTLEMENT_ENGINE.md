# Motor de liquidação (Pi → BRL → Pix)

## Fluxo

1. **PaymentIntent** criado (`POST /api/checkout/pi-intent`).
2. Pagamento Pi **verificado** (`POST /api/payments/verify`) → `verified_at` preenchido.
3. Beneficiário com **consentimento Open Finance** ativo (`POST /api/consents`…).
4. **Liquidação:** `POST /api/settlements/execute` com `intent_id`, `cpf`, `pix_key` (e opcionalmente `description`).

O serviço:

- Converte `amount_pi` → BRL com **FXService** (mesma config que o resto do projeto).
- Aplica **SETTLEMENT_FEE_RATE** (env, default `0`) sobre o bruto em BRL.
- Envia **Pix** pelo **SettlementPixPort**: mock se `OF_USE_MOCK=true`, senão **PixClient** (Open Finance).

## Campos em `PaymentIntent`

| Campo | Uso |
|--------|-----|
| `settlement_status` | `SETTLED`, `SETTLEMENT_FAILED`, etc. |
| `settled_amount_brl` | Valor líquido enviado no Pix |
| `settlement_fee_brl` | Taxa retida |
| `settlement_pix_txid` | ID da transação Pix |
| `status` | Passa a `SETTLED` após sucesso |

## Segurança

- Não liquida sem `verified_at` (Pi confirmado no backend).
- Consent tem de ser do **mesmo utilizador** que `payee_user` do intent.

## Código

- `services/pricing_service.py` — fachada sobre FX.
- `services/settlement_pix_port.py` — envio Pix (mock / real).
- `services/settlement_service.py` — orquestração.
