# Configuração do Banco de Dados PostgreSQL - Railway

**Data**: 2026-02-07

---

## 📋 Configuração Railway

O PayPi-Bridge agora suporta configuração de banco de dados via `DATABASE_URL` (padrão Railway) ou variáveis individuais.

### URL do Banco de Dados Railway

```
postgresql://postgres:RlUYVitFqMTkdDimdUYhyAZeCktXctPB@interchange.proxy.rlwy.net:45625/railway
```

---

## 🔧 Configuração

### Opção 1: DATABASE_URL (Recomendado)

No Railway, configure a variável de ambiente:

```bash
DATABASE_URL=postgresql://postgres:RlUYVitFqMTkdDimdUYhyAZeCktXctPB@interchange.proxy.rlwy.net:45625/railway
```

O Django irá automaticamente:
- Parsear a URL
- Extrair host, port, database, user, password
- Configurar SSL (sslmode=require)
- Conectar ao banco

### Opção 2: Variáveis Individuais

Alternativamente, você pode configurar:

```bash
DB_HOST=interchange.proxy.rlwy.net
DB_PORT=45625
DB_NAME=railway
DB_USER=postgres
DB_PASSWORD=RlUYVitFqMTkdDimdUYhyAZeCktXctPB
```

---

## ✅ Verificação

### Testar Conexão

```bash
cd backend
python manage.py dbshell
```

Ou via Python:

```python
from django.db import connection
connection.ensure_connection()
print("Conexão OK!")
```

### Rodar Migrations

```bash
cd backend
python manage.py migrate
```

Isso criará todas as tabelas necessárias:
- `paypibridge_*` (PaymentIntent, Consent, etc.)
- `bridge_*` (BridgeFlow, FlowEvent, etc.)
- `auth_*` (usuários Django)
- `django_*` (tabelas do Django)

---

## 🔒 Segurança

⚠️ **IMPORTANTE**: A senha do banco está exposta na URL. Certifique-se de:

1. **Nunca commitar** a `DATABASE_URL` completa no repositório
2. Usar apenas variáveis de ambiente no Railway
3. Rotacionar a senha periodicamente
4. Usar `.env` local (não commitado) para desenvolvimento

---

## 📊 Estrutura do Banco

### Tabelas Principais

**PayPi-Bridge:**
- `paypibridge_paymentintent` - Intents de pagamento
- `paypibridge_consent` - Consentimentos Open Finance
- `paypibridge_bankaccount` - Contas bancárias vinculadas
- `paypibridge_pixtransaction` - Transações Pix
- `paypibridge_webhookevent` - Eventos de webhook

**PPBridge Service:**
- `bridge_flows` - Fluxos de bridge
- `bridge_flow_events` - Eventos de auditoria
- `bridge_idempotency_records` - Registros de idempotência
- `bridge_webhook_deliveries` - Entregas de webhook

**Autenticação:**
- `auth_user` - Usuários do sistema
- `authtoken_token` - Tokens de autenticação (se usar DRF token auth)
- `token_blacklist_*` - Blacklist de tokens JWT

---

## 🚀 Próximos Passos

1. ✅ Configurar `DATABASE_URL` no Railway
2. ⏳ Rodar migrations: `python manage.py migrate`
3. ⏳ Criar superusuário: `python manage.py createsuperuser`
4. ⏳ Verificar conexão: `python manage.py dbshell`

---

**Última atualização**: 2026-02-07
