# Fila Celery — liquidação (Pi → BRL → Pix)

## Fluxo

1. `POST /api/settlements/execute` valida intent, consent e payload.
2. Com **`SETTLEMENT_ASYNC=1`** (padrão), a API responde **`202 Accepted`** com `task_id` e enfileira `process_settlement_execute`.
3. O worker executa `SettlementService.settle` (FX + Pix), atualiza `PaymentIntent` e regista `PixTransaction` quando aplicável.

## Variáveis de ambiente

| Variável | Descrição |
|----------|-----------|
| `CELERY_BROKER_URL` | Redis na mesma máquina ou rede (ex.: `redis://127.0.0.1:6379/0`) |
| `CELERY_RESULT_BACKEND` | Redis ou `django-db` (requer `django_celery_results` + migrate) |
| `SETTLEMENT_ASYNC` | `1` fila (202); `0` liquidação síncrona na request (200/400) |
| `CELERY_TASK_ALWAYS_EAGER` | `1` executa tasks na mesma thread (sem broker) |
| `CELERY_TASK_ACKS_LATE` | `1` recomendado com prefetch 1 |
| `CELERY_WORKER_PREFETCH_MULTIPLIER` | `1` recomendado para tarefas idempotentes críticas |

Durante **`manage.py test`**, `CELERY_TASK_ALWAYS_EAGER` fica ativo automaticamente para não exigir Redis.

## Sem Docker (recomendado para o teu caso)

1. **Redis** no sistema operativo (ex.: `sudo apt install redis-server` e `sudo systemctl start redis`, ou [Redis para Windows/macOS](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/)).
2. **Django** num terminal: `cd backend && python manage.py runserver`
3. **Worker** noutro terminal: `cd backend && celery -A config worker -l info`

Confirma que `CELERY_BROKER_URL` aponta para esse Redis (por defeito `redis://127.0.0.1:6379/0`).

### Sem Redis (apenas desenvolvimento)

- `CELERY_TASK_ALWAYS_EAGER=1` — as tasks correm na mesma thread que o web (sem fila real).
- Ou `SETTLEMENT_ASYNC=0` — liquidação síncrona no `POST /api/settlements/execute` (sem Celery para esse fluxo).

## Resiliência

- **Retry**: exceções inesperadas durante a task → até 3 retries com *backoff* exponencial.
- **Dead letter**: após esgotar retries, `settlement_status=SETTLEMENT_FAILED` e `metadata.settlement_dead_letter`.
- **Idempotência**: `SettlementService` recusa intents já `SETTLED`; lock curto com `select_for_update` só na fase de pré-checagem (sem bloquear a BD durante HTTP externo).

## Produção (Railway)

1. Adicionar serviço **Redis** e definir `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` no backend.
2. Adicionar serviço **Worker** com comando `celery -A config worker -l info` e as mesmas variáveis de ambiente do web (incl. `DATABASE_URL` / DB).
