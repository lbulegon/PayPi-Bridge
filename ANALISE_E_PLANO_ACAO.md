# PayPi-Bridge - Análise e Plano de Ação

**Documento original**: 2025-01-30 (análise detalhada abaixo = *corte histórico*)  
**Última revisão do cabeçalho**: 2026-03-20  
**Status atual do produto**: operacional no Railway; Fase 1 concluída; Fase 2 ~95% (falta validação com credenciais reais e Celery em produção)

> **Onde está a verdade atual**  
> Use estes ficheiros como fonte principal para estado, roadmap e próximos passos:
> - [`docs/PLANO_EVOLUCAO.md`](docs/PLANO_EVOLUCAO.md)
> - [`docs/FASE1_CONCLUSAO.md`](docs/FASE1_CONCLUSAO.md)
> - [`docs/FASE2_RESUMO_FINAL.md`](docs/FASE2_RESUMO_FINAL.md)  
> O corpo deste ficheiro (a partir de “Análise detalhada”) descreve sobretudo o projeto na época do blueprint; mantido como referência de decisões e riscos.

---

## 📋 RESUMO EXECUTIVO

**PayPi-Bridge** é um gateway de On/Off-Ramp para converter pagamentos em **Pi** em **moeda fiduciária (BRL)**, com confirmação via eventos blockchain (Soroban) e liquidação bancária via **Open Finance**.

### Arquitetura
```
Pi Wallet → Soroban Contract → CCIP/Relayer → Django Backend → Open Finance → Bancos
```

### Estado Atual (resumo março 2026)
- ✅ **Backend Django/DRF**: API completa (intents, Pi, webhooks, health/admin), JWT, rate limiting, testes e CI
- ✅ **Pi / Soroban / FX**: `PiService`, relayer com RPC Soroban, `FXService`, Celery/Beat, circuit breaker no cliente Open Finance
- ✅ **Documentação e devops**: README, `.env.example`, Docker, Railway, vários guias em `docs/`
- ⚠️ **Open Finance “de rua”**: fluxo e stubs/cliente existem; **produção** exige mTLS, OAuth e sandbox/produção com banco
- ⚠️ **Próximo foco operacional**: credenciais reais, E2E, workers Celery no Railway — ver [`docs/FASE2_RESUMO_FINAL.md`](docs/FASE2_RESUMO_FINAL.md)

---

## 🔍 ANÁLISE DETALHADA

### ✅ O QUE JÁ ESTÁ IMPLEMENTADO

#### 1. Backend Django/DRF (`backend/app/paypibridge/`)

**Models** (`models.py`):
- ✅ `Consent` - Gerenciamento de consentimentos Open Finance
- ✅ `BankAccount` - Contas bancárias vinculadas
- ✅ `PaymentIntent` - Intenção de pagamento (Pi → BRL)
- ✅ `Escrow` - Escrow para garantias
- ✅ `PixTransaction` - Transações Pix

**Views** (`views.py`):
- ✅ `IntentView` - Criar PaymentIntent local
- ✅ `CCIPWebhookView` - Webhook do relayer (com validação HMAC)
- ✅ `PixPayoutView` - Criar pagamento Pix via Open Finance

**Serializers** (`serializers.py`):
- ✅ Serializers para todos os modelos principais

**Clients** (`clients/`):
- ✅ `OpenFinanceClient` - Placeholder (não funcional)
- ✅ `PixClient` - Wrapper para Open Finance
- ⚠️ `ccip.py` - Não examinado (provavelmente placeholder)

**URLs** (`urls.py`):
- ✅ `/checkout/pi-intent` - Criar intent
- ✅ `/webhooks/ccip` - Webhook do relayer
- ✅ `/payouts/pix` - Payout Pix

#### 2. Contratos Soroban (`contracts/soroban/paypi_bridge.rs`)

**Funcionalidades**:
- ✅ `create_intent()` - Criar PaymentIntent on-chain
- ✅ `confirm_delivery()` - Confirmar entrega
- ✅ `cancel_intent()` - Cancelar intent
- ✅ Eventos: `IntentCreated`, `DeliveryConfirmed`, `IntentCancelled`

**Status**: Skeleton funcional, precisa de testes e integração

#### 3. Documentação

**Diagramas**:
- ✅ `architecture.mmd` - Arquitetura do sistema
- ✅ `sequence.mmd` - Fluxo de sequência completo

**OpenAPI**:
- ✅ `openapi.yaml` - Especificação dos endpoints

**SQL**:
- ✅ `schema.sql` - DDL completo do banco de dados

---

### ⚠️ O QUE ESTÁ FALTANDO / INCOMPLETO

#### 1. Integração com Pi Network

**Problema**: O projeto não integra com a API real da Pi Network.

**Necessário**:
- Integrar com `pi-python` SDK (`/root/Source/PiNetwork/sdk/pi-python/`)
- Implementar autenticação de usuários Pi
- Validar pagamentos Pi on-chain
- Rastrear transações na blockchain Pi

**Ação**:
```python
# Usar SDK existente
from pi_python import PiNetwork

pi = PiNetwork()
pi.initialize(api_key, wallet_private_seed, "Pi Network")
```

#### 2. Open Finance - Implementação Real

**Problema**: `OpenFinanceClient` é apenas placeholder.

**Necessário**:
- Implementar mTLS (mutual TLS)
- Implementar OAuth2 flow
- Implementar consent management
- Integrar com APIs reais de ASPSP (Bancos)
- Implementar Payments Initiation API (Pix)
- Implementar Accounts/Transactions API (reconciliação)

**Recursos Necessários**:
- Certificados mTLS
- Credenciais OAuth2
- Acesso a sandbox/produção de bancos
- Conformidade com Open Banking Brasil

#### 3. CCIP/Relayer

**Problema**: Não há implementação do relayer que monitora eventos Soroban.

**Necessário**:
- Serviço que monitora eventos do contrato Soroban
- Conversão de taxa de câmbio (Pi → BRL)
- Webhook assinado com HMAC
- Idempotência e retry logic

**Opções**:
- Implementar relayer customizado
- Usar Chainlink CCIP (se disponível)
- Usar serviço de terceiros

#### 4. Segurança e Compliance

**Faltando**:
- ⚠️ KYC/AML - Verificação de identidade
- ⚠️ LGPD - Vault de dados pessoais (PII)
- ⚠️ Auditoria completa - Logs de todas as operações
- ⚠️ Rate limiting
- ⚠️ Validação de idempotência mais robusta
- ⚠️ Allowlist de IPs para webhooks

#### 5. Testes

**Faltando**:
- ⚠️ Testes unitários
- ⚠️ Testes de integração
- ⚠️ Testes end-to-end
- ⚠️ Testes de carga

#### 6. Configuração e Deploy

**Faltando**:
- ⚠️ `.env.example` (mencionado no README, não existe)
- ⚠️ Docker compose para desenvolvimento
- ⚠️ Scripts de migração Django
- ⚠️ Configuração de produção

#### 7. Monitoramento e Observabilidade

**Faltando**:
- ⚠️ Logging estruturado
- ⚠️ Métricas (Prometheus)
- ⚠️ Tracing (OpenTelemetry)
- ⚠️ Dashboard de monitoramento
- ⚠️ Alertas

---

## 🎯 PLANO DE AÇÃO

### FASE 1: Fundação e Integração Pi Network (Prioridade ALTA)

**Objetivo**: Conectar o backend com a rede Pi Network real.

**Tarefas**:
1. ✅ Integrar `pi-python` SDK no projeto
2. ✅ Criar serviço de autenticação Pi
3. ✅ Implementar validação de pagamentos Pi
4. ✅ Criar endpoint para verificar status de pagamento Pi
5. ✅ Implementar webhook da Pi Network (se disponível)

**Arquivos a Criar/Modificar**:
- `backend/app/paypibridge/services/pi_service.py` - Serviço de integração Pi
- `backend/app/paypibridge/views.py` - Adicionar endpoints Pi
- `backend/requirements.txt` - Adicionar dependências Pi

**Estimativa**: 1-2 semanas

---

### FASE 2: Open Finance - Implementação Real (Prioridade ALTA)

**Objetivo**: Substituir placeholder por implementação real de Open Finance.

**Tarefas**:
1. ✅ Obter credenciais de sandbox Open Banking
2. ✅ Implementar mTLS client
3. ✅ Implementar OAuth2 flow
4. ✅ Implementar consent management
5. ✅ Implementar Payments Initiation API (Pix)
6. ✅ Implementar Accounts/Transactions API
7. ✅ Implementar reconciliação automática

**Arquivos a Modificar**:
- `backend/app/paypibridge/clients/open_finance.py` - Implementação completa
- `backend/app/paypibridge/clients/pix.py` - Integração real
- `backend/app/paypibridge/models.py` - Adicionar campos necessários

**Dependências Externas**:
- Certificados mTLS
- Acesso a sandbox/produção bancária
- Credenciais OAuth2

**Estimativa**: 3-4 semanas

---

### FASE 3: CCIP/Relayer (Prioridade MÉDIA)

**Objetivo**: Implementar serviço que monitora eventos Soroban e dispara webhooks.

**Tarefas**:
1. ✅ Criar serviço de monitoramento de eventos Soroban
2. ✅ Integrar com API de câmbio (Pi → BRL)
3. ✅ Implementar webhook assinado com HMAC
4. ✅ Implementar idempotência e retry
5. ✅ Criar fila de processamento (Celery/RQ)

**Arquivos a Criar**:
- `backend/app/paypibridge/services/relayer.py` - Serviço relayer
- `backend/app/paypibridge/services/fx_service.py` - Serviço de câmbio
- `backend/app/paypibridge/tasks.py` - Tarefas assíncronas

**Estimativa**: 2-3 semanas

---

### FASE 4: Segurança e Compliance (Prioridade ALTA)

**Objetivo**: Implementar segurança e compliance necessários para produção.

**Tarefas**:
1. ✅ Implementar KYC/AML (integração com provedor)
2. ✅ Implementar PII vault (LGPD compliance)
3. ✅ Implementar auditoria completa
4. ✅ Implementar rate limiting
5. ✅ Melhorar validação de idempotência
6. ✅ Implementar allowlist de IPs
7. ✅ Implementar validação de assinatura HMAC robusta

**Arquivos a Criar/Modificar**:
- `backend/app/paypibridge/middleware/security.py` - Middleware de segurança
- `backend/app/paypibridge/services/kyc_service.py` - Serviço KYC
- `backend/app/paypibridge/services/pii_vault.py` - Vault de dados pessoais
- `backend/app/paypibridge/models.py` - Adicionar AuditLog

**Estimativa**: 2-3 semanas

---

### FASE 5: Testes e Qualidade (Prioridade MÉDIA)

**Objetivo**: Garantir qualidade e confiabilidade do sistema.

**Tarefas**:
1. ✅ Criar testes unitários (cobertura >80%)
2. ✅ Criar testes de integração
3. ✅ Criar testes end-to-end
4. ✅ Implementar CI/CD
5. ✅ Testes de carga e performance

**Arquivos a Criar**:
- `backend/tests/` - Estrutura de testes
- `.github/workflows/ci.yml` - CI/CD
- `docker-compose.test.yml` - Ambiente de testes

**Estimativa**: 2 semanas

---

### FASE 6: Configuração e Deploy (Prioridade MÉDIA)

**Objetivo**: Facilitar desenvolvimento e deploy.

**Tarefas**:
1. ✅ Criar `.env.example`
2. ✅ Criar `docker-compose.yml` para desenvolvimento
3. ✅ Criar scripts de setup
4. ✅ Configurar migrações Django
5. ✅ Criar configuração de produção
6. ✅ Documentar processo de deploy

**Arquivos a Criar**:
- `.env.example` - Template de variáveis de ambiente
- `docker-compose.yml` - Ambiente de desenvolvimento
- `docker-compose.prod.yml` - Ambiente de produção
- `scripts/setup.sh` - Script de setup
- `docs/DEPLOY.md` - Documentação de deploy

**Estimativa**: 1 semana

---

### FASE 7: Monitoramento e Observabilidade (Prioridade BAIXA)

**Objetivo**: Visibilidade completa do sistema em produção.

**Tarefas**:
1. ✅ Implementar logging estruturado
2. ✅ Integrar Prometheus para métricas
3. ✅ Implementar tracing (OpenTelemetry)
4. ✅ Criar dashboard (Grafana)
5. ✅ Configurar alertas

**Estimativa**: 1-2 semanas

---

## 📊 PRIORIZAÇÃO

### 🔴 CRÍTICO (Fazer Primeiro)
1. **Fase 1**: Integração Pi Network
2. **Fase 2**: Open Finance real
3. **Fase 4**: Segurança e Compliance

### 🟡 IMPORTANTE (Fazer Depois)
4. **Fase 3**: CCIP/Relayer
5. **Fase 5**: Testes
6. **Fase 6**: Configuração e Deploy

### 🟢 DESEJÁVEL (Fazer Por Último)
7. **Fase 7**: Monitoramento

---

## 🛠️ STACK TECNOLÓGICA

### Backend
- **Framework**: Django 5.0+
- **API**: Django REST Framework
- **Documentação**: drf-spectacular (OpenAPI)
- **Validação**: Pydantic
- **Banco**: PostgreSQL (via psycopg2)

### Blockchain
- **Contratos**: Soroban (Stellar)
- **Linguagem**: Rust

### Integrações
- **Pi Network**: pi-python SDK
- **Open Finance**: APIs REST (mTLS + OAuth2)
- **CCIP/Relayer**: Custom ou Chainlink

### Infraestrutura
- **Containerização**: Docker
- **Orquestração**: Docker Compose
- **CI/CD**: GitHub Actions (sugerido)

---

## 📝 PRÓXIMOS PASSOS IMEDIATOS

1. **Criar estrutura de desenvolvimento**:
   - `.env.example`
   - `docker-compose.yml`
   - Scripts de setup

2. **Integrar Pi Network SDK**:
   - Adicionar `pi-python` ao projeto
   - Criar serviço de integração
   - Implementar autenticação

3. **Melhorar documentação**:
   - README mais detalhado
   - Guia de desenvolvimento
   - Guia de deploy

4. **Criar testes básicos**:
   - Testes unitários dos models
   - Testes das views principais

---

## ⚠️ RISCOS E DEPENDÊNCIAS

### Riscos Técnicos
- **Open Finance**: Complexidade alta, requer certificados e credenciais
- **Soroban**: Tecnologia nova, pode ter limitações
- **Pi Network**: API pode mudar, documentação pode estar incompleta

### Dependências Externas
- Acesso a sandbox/produção Open Banking
- Certificados mTLS
- Credenciais OAuth2
- API de câmbio (Pi → BRL)
- Serviço KYC/AML

### Riscos de Negócio
- Regulamentação Open Banking pode mudar
- Taxa de câmbio Pi pode ser volátil
- Compliance LGPD e regulatório

---

## 📚 RECURSOS E REFERÊNCIAS

### Documentação
- [Plano de evolução (estado atual)](docs/PLANO_EVOLUCAO.md)
- [Fase 1 — conclusão](docs/FASE1_CONCLUSAO.md)
- [Fase 2 — resumo final](docs/FASE2_RESUMO_FINAL.md)
- [Pi Network SDK Python](../sdk/pi-python/README.md)
- [Pi Platform Docs](../docs/pi-platform-docs/)
- [Open Banking Brasil](https://www.bcb.gov.br/estabilidadefinanceira/openbanking)

### Projetos Relacionados
- `pi-python` - SDK Python para Pi Network
- `demo` - Exemplo de integração Pi Network

---

**Última atualização do rodapé**: 2026-03-20  
**Próxima revisão**: Alinhar secção “Análise detalhada” ao código ou arquivar como histórico-only
