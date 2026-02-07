# Setup Local e Migrations

**Data**: 2026-02-07

---

## 🚀 Configuração Inicial

### 1. Instalar Dependências

```bash
cd backend
pip install -r requirements.txt
# ou
pip3 install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Certifique-se de que o arquivo `.env` está configurado na raiz do projeto:

```bash
# O arquivo .env já deve conter:
DATABASE_URL=postgresql://postgres:RlUYVitFqMTkdDimdUYhyAZeCktXctPB@interchange.proxy.rlwy.net:45625/railway
```

### 3. Executar Migrations

#### Opção A: Script Automatizado

```bash
./scripts/setup_and_migrate.sh
```

#### Opção B: Manual

```bash
cd backend
python manage.py migrate
# ou
python3 manage.py migrate
```

---

## ✅ Verificar Conexão

### Testar Conexão com o Banco

```bash
cd backend
python manage.py check --database default
```

### Acessar Shell do Banco

```bash
cd backend
python manage.py dbshell
```

---

## 🔧 Comandos Úteis

### Criar Superusuário

```bash
cd backend
python manage.py createsuperuser
```

### Rodar Servidor de Desenvolvimento

```bash
cd backend
python manage.py runserver
# ou em uma porta específica:
python manage.py runserver 8000
```

### Ver Status das Migrations

```bash
cd backend
python manage.py showmigrations
```

### Criar Nova Migration

```bash
cd backend
python manage.py makemigrations
```

### Aplicar Migrations Específicas

```bash
cd backend
python manage.py migrate app_name
```

---

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'django'"

**Solução**: Instale as dependências:
```bash
cd backend
pip install -r requirements.txt
```

### Erro: "could not connect to server"

**Solução**: Verifique:
1. Se `DATABASE_URL` está correta no `.env`
2. Se o banco Railway está acessível
3. Se há firewall bloqueando a conexão

### Erro: "relation does not exist"

**Solução**: Execute as migrations:
```bash
cd backend
python manage.py migrate
```

### Erro: "password authentication failed"

**Solução**: Verifique se a senha na `DATABASE_URL` está correta.

---

## 📋 Checklist de Setup

- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Arquivo `.env` configurado com `DATABASE_URL`
- [ ] Conexão com banco testada (`python manage.py check`)
- [ ] Migrations executadas (`python manage.py migrate`)
- [ ] Superusuário criado (opcional, `python manage.py createsuperuser`)

---

## 🚢 Railway Deployment

No Railway, as migrations são executadas automaticamente durante o deploy se você configurar:

```bash
# No Procfile ou Railway settings:
release: cd backend && python manage.py migrate
web: cd backend && ./start.sh
```

Ou configure no Railway Dashboard:
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `cd backend && python manage.py migrate && ./start.sh`

---

**Última atualização**: 2026-02-07
