# PiBridge Pay — Blueprint (Pi → CCIP/Relayer → Open Finance → Bancos)

Gateway de On/Off-Ramp para converter pagamentos em **Pi** em **moeda fiduciária**,
com confirmação via evento (relayer/CCIP) e liquidação bancária por **Open Finance**.

## Conteúdo
- backend/ (Django + DRF: models, views, urls, clients)
- contracts/ (Soroban skeleton: PaymentIntent + eventos)
- docs/ (diagramas Mermaid de sequência e arquitetura)
- sql/ (DDL inicial)
- openapi/ (OpenAPI 3.0 dos endpoints)
- postman/ (coleção para testes)

## Quickstart (dev)
1. Crie um projeto Django e adicione `backend/app/pibridge` como app.
2. `pip install -r backend/requirements.txt`
3. Copie `.env.example` para `.env` e preencha.
4. Inclua `path("api/", include("pibridge.urls")),` no seu `urls.py` raiz.
5. Rode migrações e teste com a coleção Postman.

## Fluxo alto nível
1) DApp cria **PaymentIntent** on-chain (Soroban) → emite evento.
2) Relayer (CCIP ou custom) envia webhook assinado para `/webhooks/ccip`.
3) Backend valida e inicia pagamento via **Open Finance** (Pix/Payments Initiation).
4) Liquidação bancária confirma → atualiza `PaymentIntent` para `SETTLED`.
5) Reconciliação via `accounts/transactions` (Open Finance).

## Segurança
- Webhook com HMAC + allowlist IP.
- Open Finance com mTLS + OAuth2 + consents escopados.
- KYC/AML, LGPD (PII vault), auditoria e idempotência.
