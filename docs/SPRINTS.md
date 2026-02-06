# Sprints – PayPi-Bridge

Sprints para seguir um a um. Cada sprint tem objetivo, tarefas e critério de conclusão.

---

## Visão geral

| Sprint | Foco | Duração sugerida |
|--------|------|------------------|
| **1** | Fundação e Pi ativo | 1 semana |
| **2** | Fluxo checkout + verify Pi | 1 semana |
| **3** | Open Finance (sandbox) | 2 semanas |
| **4** | Webhook CCIP / Relayer | 1–2 semanas |
| **5** | Testes e qualidade | 1 semana |
| **6** | Segurança e preparação para deploy | 1 semana |

---

## Sprint 1 – Fundação e Pi ativo

**Objetivo:** Ambiente estável, Pi Network configurado e testado via formulários.

**Tarefas:**
- [x] Docker sobe sem conflito de portas (backend na 9080, db/redis internos)
- [x] Migrações aplicadas (`docker compose exec backend python manage.py migrate`)
- [x] Página inicial (/) e /forms/ acessíveis
- [x] GET /api/pi/status retorna `configured: true` ou `false` + message
- [x] GET /api/pi/balance: com Pi configurado retorna saldo; sem config retorna 503 com mensagem clara
- [ ] .env com PI_API_KEY, PI_WALLET_PRIVATE_SEED, PI_NETWORK preenchidos (ou documentado onde obter)
- [x] Usuário de teste no banco (ex.: `createsuperuser` com id 1) para uso no checkout

**Entregáveis:**
- Backend estável em Docker
- Formulários de teste com Status Pi, Saldo Pi, Criar Intent, Verificar pagamento
- Documentação: `docs/INTEGRACAO_PI_NETWORK.md` e `docs/SPRINTS.md`

**Concluído quando:** Status Pi e Saldo Pi respondem corretamente em /forms/ (com ou sem credenciais).

---

## Sprint 2 – Fluxo checkout + verify Pi

**Objetivo:** Criar PaymentIntent pela API/form e vincular um pagamento Pi ao intent (verify).

**Tarefas:**
- [x] POST /api/checkout/pi-intent retorna 201 e intent_id (com payee_user_id válido)
- [x] Form "Criar intent" em /forms/ funciona e exibe intent_id no resultado
- [x] POST /api/payments/verify com payment_id e intent_id válidos atualiza o PaymentIntent (payer_address, metadata com pi_payment_id)
- [x] Tratamento claro quando intent não existe, payment não existe ou payment cancelado
- [x] (Opcional) Listar intents: GET /api/intents ou listagem mínima para testes

**Entregáveis:**
- Fluxo: criar intent → (pagamento Pi externo) → verify → intent atualizado
- Formulários de teste cobrindo criar intent e verify

**Concluído quando:** É possível criar um intent pelo form e simular/verificar um pagamento Pi vinculado a esse intent.

---

## Sprint 3 – Open Finance (sandbox)

**Objetivo:** Consents e Pix payout utilizáveis em sandbox (ou mock para desenvolvimento).

**Tarefas:**
- [x] Obter credenciais de sandbox Open Banking (ou definir mock)
- [x] OpenFinanceClient e PixClient conectados a um provedor sandbox (ou mock retornando sucesso)
- [x] POST /api/consents cria consent e retorna consent_id
- [x] POST /api/payouts/pix cria pagamento Pix (sandbox/mock) e retorna txid/status
- [x] GET /api/consents lista consents do usuário (com autenticação ou usuário de teste)
- [x] Documentar variáveis de ambiente Open Finance no .env.example

**Entregáveis:**
- Fluxo consent → link bank account → payout Pix (em sandbox ou mock)
- Documentação: variáveis OF_* e como obter credenciais sandbox

**Concluído quando:** Um payout Pix (ou mock) é disparado com sucesso a partir da API.

---

## Sprint 4 – Webhook CCIP / Relayer

**Objetivo:** Receber eventos (ex.: Soroban) em /api/webhooks/ccip e processar (atualizar intent, opcionalmente disparar Pix).

**Tarefas:**
- [x] POST /api/webhooks/ccip valida HMAC (header X-Signature) com CCIP_WEBHOOK_SECRET
- [x] Payload do webhook atualiza PaymentIntent (ex.: intent_id, fx_quote, status)
- [x] Idempotência: mesmo evento não processa duas vezes (ex.: por intent_id + id do evento)
- [ ] (Opcional) Disparar payout Pix quando intent for CONFIRMED/SETTLED
- [x] Documentar formato esperado do payload e como gerar HMAC para testes

**Entregáveis:**
- Webhook CCIP funcional com validação HMAC e idempotência
- Exemplo de payload e script ou Postman para testar o webhook

**Concluído quando:** Um POST em /api/webhooks/ccip com HMAC válido atualiza o intent (e opcionalmente dispara Pix).

---

## Sprint 5 – Testes e qualidade

**Objetivo:** Testes automatizados e qualidade de código para os fluxos principais.

**Tarefas:**
- [ ] Testes unitários para PiService (get_balance, verify_payment com mock)
- [ ] Testes para views: criar intent, verify payment, pi/status, pi/balance
- [ ] Testes para serializers e validações de payload
- [ ] Cobertura mínima definida (ex.: >70% em services e views)
- [ ] Execução de testes no CI ou via `docker compose exec backend python manage.py test`

**Entregáveis:**
- Suite de testes rodando com `python manage.py test`
- (Opcional) CI (ex.: GitHub Actions) rodando testes em todo push

**Concluído quando:** Testes passando e cobrindo criar intent, verify Pi, status/balance e webhook.

---

## Sprint 6 – Segurança e preparação para deploy

**Objetivo:** Reforçar segurança e deixar o projeto pronto para deploy em produção.

**Tarefas:**
- [ ] ALLOWED_HOSTS e DEBUG via ambiente; SECRET_KEY forte em produção
- [ ] Endpoints sensíveis (consents, payouts) com autenticação (token ou session)
- [ ] Rate limiting em /api/ (ex.: django-ratelimit ou nginx)
- [ ] CCIP: allowlist de IPs ou validação extra (CCIP_RELAYER_WHITELIST)
- [ ] Logging estruturado (request_id, endpoint, status, tempo)
- [ ] Documentar deploy (docker-compose.prod, variáveis, backup DB)
- [ ] (Opcional) HTTPS e certificados (Let's Encrypt ou proxy)

**Entregáveis:**
- Checklist de segurança aplicado
- Documento de deploy (passos, env, backup)
- (Opcional) docker-compose.prod ou guia para produção

**Concluído quando:** Aplicação rodando em ambiente tipo produção com segurança básica e documentação de deploy.

---

## Como usar este documento

1. **Sprint atual:** marque com um comentário ou título "Sprint atual: X" no topo do arquivo (ou num README).
2. **Tarefas:** use `- [x]` quando concluir uma tarefa.
3. **Concluído quando:** só considere o sprint fechado quando o critério "Concluído quando" for atendido.
4. **Ajustes:** adapte durações e tarefas ao seu ritmo; pode quebrar um sprint em dois ou juntar itens.

---

## Ordem recomendada

Seguir na ordem **Sprint 1 → 2 → 3 → 4 → 5 → 6**. Os sprints 3 e 4 podem trocar de ordem se a prioridade for relayer antes de Open Finance.
