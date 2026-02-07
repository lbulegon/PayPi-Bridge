# Sincronização de Requirements

## ⚠️ IMPORTANTE

O Railway usa o arquivo `requirements.txt` da **raiz do projeto**, não o `backend/requirements.txt`.

Quando você adicionar uma nova dependência em `backend/requirements.txt`, **sempre** adicione também ao `requirements.txt` da raiz.

## 🔄 Sincronização Automática

### Script de Sincronização

Existe um script Python que sincroniza automaticamente os dois arquivos:

```bash
# Verificar se há diferenças (não modifica arquivos)
python scripts/sync_requirements.py --check

# Sincronizar automaticamente
python scripts/sync_requirements.py
```

### Quando Usar

1. **Após adicionar dependência em `backend/requirements.txt`**
   ```bash
   python scripts/sync_requirements.py
   ```

2. **Antes de fazer commit** (o pre-commit hook verifica automaticamente)

3. **No CI/CD** (GitHub Actions verifica automaticamente)

## 📋 Processo Recomendado

1. Adicionar dependência em `backend/requirements.txt`
2. Executar `python scripts/sync_requirements.py`
3. Fazer commit de ambos os arquivos

## 🛡️ Proteções Automáticas

### Pre-commit Hook

Um hook Git verifica automaticamente antes de cada commit se `backend/requirements.txt` foi modificado e se `requirements.txt` da raiz está sincronizado.

### CI/CD Check

O GitHub Actions verifica automaticamente em cada PR se os requirements estão sincronizados.

## ❌ Erro Comum

**Erro**: `ModuleNotFoundError: No module named 'django_xxx'`

**Causa**: Dependência adicionada apenas em `backend/requirements.txt`, mas não no `requirements.txt` da raiz.

**Solução**: Execute `python scripts/sync_requirements.py` e faça commit.

## 📝 Estrutura dos Arquivos

```
PayPi-Bridge/
├── requirements.txt          ← Usado pelo Railway (DEVE estar sincronizado)
└── backend/
    └── requirements.txt      ← Requirements do backend Django
```

## 🔍 Verificação Manual

Para verificar manualmente se há pacotes faltando:

```bash
# Listar pacotes em backend/requirements.txt
grep -v "^#" backend/requirements.txt | grep -v "^$" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1 | tr -d ' ' | sort

# Listar pacotes em requirements.txt da raiz
grep -v "^#" requirements.txt | grep -v "^$" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1 | tr -d ' ' | sort

# Comparar
diff <(grep -v "^#" backend/requirements.txt | grep -v "^$" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1 | tr -d ' ' | sort) \
     <(grep -v "^#" requirements.txt | grep -v "^$" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1 | tr -d ' ' | sort)
```

Ou simplesmente use o script:

```bash
python scripts/sync_requirements.py --check
```
