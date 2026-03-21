# PayPi-Bridge — Resumo de infraestrutura (para cruzar com outro contexto)

**Objetivo:** texto autocontido para colar noutro chat (ex.: ChatGPT) e alinhar com diagramas, Terraform, ou outra documentação de infra.

**Repo:** `PayPi-Bridge` (backend Django em `backend/`). **Raiz do projeto** também tem `requirements.txt` usado pelo Railway.

---

## 1. Stack de runtime

| Componente | Detalhe |
|------------|---------|
| Linguagem | Python **3.11** (`runtime.txt`: 3.11.9) |
| Framework | **Django 5+**, **Django REST Framework** |
| Servidor HTTP (produção) | **Gunicorn** (`backend/start.sh`: bind `0.0.0.0:$PORT`) |
| Servidor (dev local) | `python manage.py runserver` |
| Estáticos | **WhiteNoise** + `collectstatic` no arranque |
| API docs | **drf-spectacular** → `/api/schema/swagger-ui/` |

---

## 2. Serviços e dependências

| Serviço | Função | Dev local | Produção típica (Railway) |
|---------|--------|-----------|---------------------------|
| **PostgreSQL 15** | BD principal Django | Instância local ou URL remota; migrações Django | Plugin PostgreSQL ou `DATABASE_URL` |
| **Redis 7** | Broker/resultado Celery, cache FX | `redis-server` local ou URL remota | Serviço Redis (variáveis `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND`) |
| **Processo web** | HTTP API + páginas HTML em `config/urls.py` | `runserver` (porta local à escolha) | `$PORT` definido pela plataforma |
| **Celery worker** | Tarefas assíncronas (webhooks Pi, Soroban, Pix, FX) | `celery -A config worker` num terminal separado | **Serviço separado** recomendado: mesmo comando + **beat** para agendamentos |
| **Celery Beat** | `monitor_soroban_events` (30s), `process_incomplete_payments` (5min), `update_fx_rates` (5min) | Opcional em dev | Sem beat em prod, tarefas periódicas não correm |

---

## 3. Deploy Railway (padrão do repo)

- **`Procfile`:**  
  - `release:` `cd backend && python manage.py migrate --noinput`  
  - `web:` `cd backend && ./start.sh` (collectstatic + gunicorn)
- **Dependências:** instalar a partir da **`requirements.txt` da raiz** (sincronizado com `backend/requirements.txt` via `scripts/sync_requirements.py`).
- **Proxy:** Django usa `SECURE_PROXY_SSL_HEADER`, `USE_X_FORWARDED_HOST`, `USE_X_FORWARDED_PORT` para HTTPS atrás do proxy Railway.
- **Hosts:** `ALLOWED_HOSTS` inclui `.railway.app` e domínio explícito de deploy; `CSRF_TRUSTED_ORIGINS` inclui `*.railway.app`.
- **Middleware:** `RailwayHostValidationMiddleware` + CORS + logging com `request_id`.

---

## 4. Desenvolvimento local (sem Compose no repo)

- Postgres e Redis instalados ou geridos na cloud; venv Python; `manage.py runserver` + worker Celery quando necessário.
- Ver `README.md` e `docs/DEVELOPMENT.md`.

---

## 5. Base de dados

- **Preferido em PaaS:** `DATABASE_URL` (postgresql…); parsing em `settings.py` com `sslmode` automático (`disable` para host `.railway.internal`, `require` caso contrário se não houver override).
- **Alternativa:** `DB_*` ou variáveis **`PG*`** (libpq), com `CONN_MAX_AGE=600`.
- Migrações: Django (`app.paypibridge` + apps contrib). `sql/schema.sql` como referência DDL legada.

---

## 6. Variáveis de ambiente (grupos)

*(Nomes exatos no `.env.example` da raiz.)*

- **Core:** `DJANGO_SECRET` / `DJANGO_SECRET_KEY`, `DEBUG`, `ENV`, `ALLOWED_HOSTS`
- **Pi Network:** `PI_API_KEY`, `PI_WALLET_PRIVATE_SEED`, `PI_NETWORK` (`Pi Testnet` | `Pi Network`)
- **Open Finance:** `OF_USE_MOCK`, `OF_BASE_URL`, OAuth, paths mTLS (`OF_MTLS_*`)
- **Webhooks CCIP:** `CCIP_WEBHOOK_SECRET`, `CCIP_RELAYER_WHITELIST`
- **Celery/Redis:** `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` (default local `redis://localhost:6379/0`)
- **Observabilidade:** `SENTRY_DSN` (opcional)
- **PPBridge (serviço extra):** `PPBRIDGE_API_KEY_*`, webhooks HMAC, log level

---

## 7. CI/CD

- **GitHub Actions** `.github/workflows/ci.yml`: push/PR em `main` e `develop`; Postgres 15 + Redis 7; Python 3.11; `migrate` + testes com coverage; lint (flake8, black, isort).
- Workflow adicional: `sync_requirements.yml` (sincronizar requirements raiz/backend).

---

## 8. Integrações externas (ângulo infra)

- **Pi:** SDK Python (`pi_python`); path local `backend/pi_sdk/` no código; em imagens mínimas pode faltar — validar build.
- **Stellar/Soroban:** `stellar-sdk`; relayer consulta RPC (env específicos no serviço relayer).
- **Open Finance:** HTTP client com circuit breaker; mock quando `OF_USE_MOCK=true`.

---

## 9. Endpoints de saúde (dois níveis)

- **`GET /health/`** — resposta simples JSON (`ok`); útil para probes de plataforma.
- **`GET /api/health`** — health agregado (Pi, OF, Soroban, DB, cache, Celery, etc.).

---

## 10. Lacunas comuns em produção

1. **Celery worker/beat** não provisionados → webhooks assíncronos e jobs periódicos não executam.
2. **Pi** sem `PI_API_KEY` / `PI_WALLET_PRIVATE_SEED` → `/api/pi/status` com `configured: false`, `/api/pi/balance` → 503.
3. **Redis** inacessível → Celery e cache FX degradados.
4. **Requisitos na raiz** desatualizados em relação a `backend/requirements.txt` → falhas no deploy Railway.

---

## 11. O que pedir ao outro modelo

Sugerir comparação com:

- Topologia (VPC, subnets, SG/firewall)
- Serviços geridos vs self-hosted (Postgres, Redis)
- Segredos (Secret Manager vs env plain)
- Observabilidade (logs, métricas, alertas)
- HA do worker Celery e fila Redis
- TLS termination e domínio custom

---

**Nota de segurança:** evitar commitar `DATABASE_URL` ou passwords em markdown; usar placeholders neste resumo e rotacionar qualquer credencial já exposta em histórico git.

**Última geração do documento:** 2026-03-20 (espelha o estado do código no repositório).
