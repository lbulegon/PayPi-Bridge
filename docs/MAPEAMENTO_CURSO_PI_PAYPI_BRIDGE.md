# Mapeamento: curso técnico Pi/Stellar ↔ PayPi-Bridge

Este ficheiro liga o conteúdo de [`PI-NETWORK-CURSO-TECNICO.md`](PI-NETWORK-CURSO-TECNICO.md) ao que o **PayPi-Bridge** implementa hoje e ao que faz sentido evoluir.

---

## Duas camadas diferentes (importante)

| Camada | O que o curso cobre | O que o PayPi-Bridge usa |
|--------|---------------------|---------------------------|
| **Ledger / nó** | `stellar-core`, Horizon, PostgreSQL, SCP, quorum, sync, portas P2P | Não executa nó; não depende do teu Pi Node para a API Django |
| **Aplicação / plataforma** | Menciona onramps/liquidez de forma educacional | **`pi-python`** (`PiService`): pagamentos, verificação por `payment_id`, rede `Pi Testnet` / `Pi Network` via env |

Conclusão: o curso **não substitui** a documentação da Pi Platform nem o código em `backend/app/paypibridge/services/pi_service.py`. Ele **complementa** com contexto de rede, segurança operacional e fiabilidade.

---

## Onde o curso ajuda a avançar o produto

### 1. Alinhamento de rede e mental model

- O curso explica `NETWORK_PASSPHRASE` e isolamento Pi vs Stellar “genérico”.
- No bridge, `PI_NETWORK` (ex.: `Pi Testnet` vs `Pi Network`) deve estar **coerente** com as credenciais e com o ambiente que a Pi Platform espera.
- **Ação**: documentar no `.env.example` / `docs/CONFIGURACAO_CREDENCIAIS.md` a correspondência explícita entre rede escolhida no node (se existir) e `PI_NETWORK` no backend.

### 2. Observabilidade e saúde (Módulos 5 e 6)

- Ideias do curso: estados Synced/Catching, lag de ingest, logs vs compatibilidade de versão.
- No bridge já existem health checks e integração Pi em `PiService`.
- **Ação evolutiva**: se no futuro quiseres **confirmação independente** no ledger (além da API Platform), podes expor um passo opcional que consulta **Horizon** de uma instância confiável — isso exige URL de Horizon, parsing de transações e política de confiança; o curso dá a base conceitual (não é obrigatório para o MVP).

### 3. Segurança operacional (Módulo 6)

- Segredos (`PI_WALLET_PRIVATE_SEED`, `PI_API_KEY`), permissões de ficheiros, não vazar seeds em logs.
- **Ação**: rever logs em `pi_service.py` (evitar `print` com dados sensíveis; preferir logger sem segredos) e garantir que o material do curso está alinhado com a política de secrets no Railway/Docker.

### 4. On-ramp / liquidez (Módulo 8)

- O curso descreve o **padrão** de onramps (custódia, compliance, risco).
- O PayPi-Bridge é precisamente um **gateway** Pi → BRL (Open Finance). O módulo 8 ajuda a **enquadrar** requisitos de negócio e risco junto da Fase 3 do [`PLANO_EVOLUCAO.md`](PLANO_EVOLUCAO.md) (KYC/LGPD).

### 5. Labs A/B/C

- Úteis para quem **opera** um Pi Node na mesma organização que o bridge (baseline de saúde, firewall, versões).
- Não desbloqueiam por si um endpoint novo no Django; melhoram **confiabilidade percebida** da stack e reduzem incidentes “a rede está estranha”.

---

## O que o curso não cobre (e o projeto precisa)

- **Pi Platform API** (criar/verificar pagamentos, webhooks oficiais): seguir SDK + docs Pi + o que já está em `FASE2_RESUMO_FINAL.md`.
- **Open Finance Brasil** (mTLS, OAuth, Pix): fora do âmbito do curso Stellar/node.
- **Soroban / relayer** no bridge: outro eixo; o curso é Stellar clássico + Pi Node, não contratos Soroban em detalhe.

---

## Próximos passos sugeridos (prioridade)

1. **Curto prazo**: validar E2E com credenciais reais na mesma rede que `PI_NETWORK` (como em [`FASE2_RESUMO_FINAL.md`](FASE2_RESUMO_FINAL.md)).
2. **Documentação**: uma secção no README ou em `CONFIGURACAO_CREDENCIAIS.md` — “Node operators vs app developers” com link para este mapeamento e para o curso.
3. **Opcional técnico**: após estabilizar Platform API, avaliar **verificação complementar via Horizon** (só se houver requisito de auditoria on-chain explícito).

---

**Última atualização**: 2026-03-20
