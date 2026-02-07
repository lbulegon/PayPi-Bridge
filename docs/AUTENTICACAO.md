# Sistema de Autenticação - PayPi-Bridge

**Data**: 2026-02-07  
**Status**: ✅ Implementado

---

## 📋 Visão Geral

O PayPi-Bridge implementa autenticação baseada em **JWT (JSON Web Tokens)** usando `djangorestframework-simplejwt`. O sistema suporta:

- ✅ Registro de novos usuários
- ✅ Login com username ou email
- ✅ Tokens JWT (access + refresh)
- ✅ Refresh de tokens
- ✅ Logout com invalidação de tokens
- ✅ Perfil do usuário (obter/atualizar)
- ✅ Alteração de senha
- ✅ Verificação de autenticação

---

## 🔐 Endpoints de Autenticação

### 1. Registro

**POST** `/api/auth/register/`

Cria um novo usuário e retorna tokens JWT.

**Body:**
```json
{
  "username": "usuario123",
  "email": "usuario@example.com",
  "password": "SenhaSegura123!",
  "password_confirm": "SenhaSegura123!",
  "first_name": "João",
  "last_name": "Silva"
}
```

**Response 201:**
```json
{
  "message": "Usuário criado com sucesso",
  "user": {
    "id": 1,
    "username": "usuario123",
    "email": "usuario@example.com",
    "first_name": "João",
    "last_name": "Silva",
    "date_joined": "2026-02-07T00:00:00Z",
    "is_active": true
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Validações:**
- Username único
- Email único e válido
- Senha deve atender critérios de segurança (Django validators)
- Senhas devem coincidir

**Rate Limit:** 5 requisições/minuto por IP

---

### 2. Login

**POST** `/api/auth/login/`

Autentica usuário e retorna tokens JWT.

**Body:**
```json
{
  "username": "usuario123",
  "password": "SenhaSegura123!"
}
```

**OU:**
```json
{
  "email": "usuario@example.com",
  "password": "SenhaSegura123!"
}
```

**Response 200:**
```json
{
  "message": "Login realizado com sucesso",
  "user": {
    "id": 1,
    "username": "usuario123",
    "email": "usuario@example.com",
    "first_name": "João",
    "last_name": "Silva",
    "date_joined": "2026-02-07T00:00:00Z",
    "is_active": true
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Erros:**
- `INVALID_CREDENTIALS` (401) - Credenciais inválidas
- `USER_INACTIVE` (403) - Usuário inativo

**Rate Limit:** 10 requisições/minuto por IP

---

### 3. Refresh Token

**POST** `/api/auth/refresh/`

Renova o access token usando o refresh token.

**Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response 200:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Rate Limit:** 30 requisições/minuto por IP

---

### 4. Logout

**POST** `/api/auth/logout/`

Invalida o refresh token (requer autenticação).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response 200:**
```json
{
  "message": "Logout realizado com sucesso"
}
```

---

### 5. Perfil do Usuário

**GET** `/api/auth/me/`

Obtém dados do usuário autenticado.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response 200:**
```json
{
  "id": 1,
  "username": "usuario123",
  "email": "usuario@example.com",
  "first_name": "João",
  "last_name": "Silva",
  "date_joined": "2026-02-07T00:00:00Z",
  "is_active": true
}
```

**PUT/PATCH** `/api/auth/me/`

Atualiza dados do usuário autenticado.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "first_name": "João Pedro",
  "last_name": "Silva Santos",
  "email": "novoemail@example.com"
}
```

**Response 200:**
```json
{
  "id": 1,
  "username": "usuario123",
  "email": "novoemail@example.com",
  "first_name": "João Pedro",
  "last_name": "Silva Santos",
  "date_joined": "2026-02-07T00:00:00Z",
  "is_active": true
}
```

**Validações:**
- Email deve ser único (se alterado)
- Não é possível alterar username

---

### 6. Alterar Senha

**POST** `/api/auth/change-password/`

Altera a senha do usuário autenticado.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "old_password": "SenhaAntiga123!",
  "new_password": "NovaSenhaSegura123!",
  "new_password_confirm": "NovaSenhaSegura123!"
}
```

**Response 200:**
```json
{
  "message": "Senha alterada com sucesso"
}
```

**Validações:**
- Senha antiga deve estar correta
- Nova senha deve atender critérios de segurança
- Senhas devem coincidir

**Rate Limit:** 5 requisições/minuto por usuário

---

### 7. Verificar Autenticação

**GET** `/api/auth/check/`

Verifica se usuário está autenticado e retorna dados.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response 200:**
```json
{
  "authenticated": true,
  "user": {
    "id": 1,
    "username": "usuario123",
    "email": "usuario@example.com",
    "first_name": "João",
    "last_name": "Silva",
    "date_joined": "2026-02-07T00:00:00Z",
    "is_active": true
  }
}
```

---

## 🔑 Uso de Tokens

### Headers

Para endpoints que requerem autenticação, inclua o access token:

```
Authorization: Bearer <access_token>
```

### Exemplo com cURL

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario123",
    "password": "SenhaSegura123!"
  }'

# Usar token em requisição autenticada
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### Exemplo com JavaScript

```javascript
// Login
const loginResponse = await fetch('/api/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'usuario123',
    password: 'SenhaSegura123!'
  })
});

const { tokens, user } = await loginResponse.json();

// Salvar tokens
localStorage.setItem('access_token', tokens.access);
localStorage.setItem('refresh_token', tokens.refresh);

// Usar em requisições autenticadas
const response = await fetch('/api/auth/me/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
});
```

---

## ⚙️ Configuração

### Tokens JWT

Configurado em `backend/config/settings.py`:

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),  # Access token válido por 1 hora
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),    # Refresh token válido por 7 dias
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ROTATE_REFRESH_TOKENS": True,                   # Gera novo refresh token a cada refresh
    "BLACKLIST_AFTER_ROTATION": True,                # Invalida refresh token antigo
    "UPDATE_LAST_LOGIN": True,                       # Atualiza last_login
}
```

### Permissões Padrão

Por padrão, todos os endpoints requerem autenticação:

```python
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}
```

Endpoints públicos devem usar `permission_classes = [AllowAny]`.

---

## 🔒 Segurança

### Validação de Senha

O Django valida senhas usando validators padrão:
- Mínimo de caracteres
- Não pode ser muito comum
- Não pode ser muito similar a informações do usuário
- Deve conter uma mistura de caracteres

### Rate Limiting

- Registro: 5 req/min por IP
- Login: 10 req/min por IP
- Refresh: 30 req/min por IP
- Alterar senha: 5 req/min por usuário

### Blacklist de Tokens

Tokens refresh são invalidados após logout ou rotação, usando `rest_framework_simplejwt.token_blacklist`.

---

## 📊 Fluxo Completo

### 1. Registro

```bash
POST /api/auth/register/
→ Retorna tokens JWT
```

### 2. Login

```bash
POST /api/auth/login/
→ Retorna tokens JWT
```

### 3. Usar Access Token

```bash
GET /api/auth/me/
Authorization: Bearer <access_token>
→ Retorna dados do usuário
```

### 4. Refresh Token (quando access token expira)

```bash
POST /api/auth/refresh/
Body: { "refresh": "<refresh_token>" }
→ Retorna novo access token
```

### 5. Logout

```bash
POST /api/auth/logout/
Authorization: Bearer <access_token>
Body: { "refresh": "<refresh_token>" }
→ Invalida refresh token
```

---

## 🧪 Testes

### Exemplo de Teste

```python
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_register(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Test123!@#',
            'password_confirm': 'Test123!@#'
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn('tokens', response.data)
    
    def test_login(self):
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Test123!@#'
        )
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'Test123!@#'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('tokens', response.data)
```

---

## 📝 Próximos Passos

- [ ] Implementar recuperação de senha (reset password)
- [ ] Implementar verificação de email
- [ ] Adicionar 2FA (Two-Factor Authentication)
- [ ] Implementar OAuth2 (Google, GitHub, etc.)
- [ ] Adicionar endpoints de listagem de sessões ativas
- [ ] Implementar logout de todas as sessões

---

**Última atualização**: 2026-02-07
