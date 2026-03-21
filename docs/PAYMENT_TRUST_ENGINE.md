# Payment Trust Engine (Pi Platform + Horizon opcional)

## Fluxo

1. **Pi Platform** — `POST /api/payments/verify` continua a usar `PiService.verify_payment`; só após `transaction_verified` corre o orquestrador.
2. **Horizon (opcional)** — Se `ENABLE_LEDGER_VERIFICATION=true` e `HORIZON_URL` apontar para um Horizon compatível com o ledger onde a tx existe, o sistema consulta `GET /transactions/{txid}` e `.../operations` e pode elevar o nível de confiança.

## Níveis (`PaymentIntent.confidence_level`)

| Valor | Significado |
|--------|-------------|
| `medium_trust` | Pi Platform verificada; ledger desligado ou sem txid |
| `high_trust` | Pi Platform + transação encontrada no Horizon |
| `medium_trust_ledger_tx_not_found` | Pi ok; tx não encontrada (ex.: HTTP 404 no Horizon) |
| `medium_trust_ledger_unavailable` | Pi ok; erro de rede/outro HTTP no Horizon |

`ledger_checked` no modelo é `true` apenas quando a tx foi **encontrada** no ledger.

## Endpoints

- `GET /health/bridge` — `pi_api`, `ledger`, `latency_ms`, `confidence_mode` (`hybrid` | `platform_only`).
- `GET /api/payments/ledger/<txid>` — auditoria read-only no Horizon (503 se ledger desligado).

## Variáveis

Ver `.env.example`: `ENABLE_LEDGER_VERIFICATION`, `HORIZON_URL`, `LEDGER_VERIFY_TIMEOUT`, `STRICT_LEDGER_AMOUNT_MATCH`.

**Importante:** o Horizon público da Stellar **não** indexa o ledger Pi. Configure o URL correto para o ambiente Pi que estás a usar.

## Código

- `services/ledger_verifier.py`
- `services/payment_orchestrator.py` (`PaymentTrustOrchestrator`, `get_ledger_verifier`)
