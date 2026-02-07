from django.http import JsonResponse, HttpResponse
from django.urls import path, include
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


def health_view(request):
    return JsonResponse({"status": "ok"})


def home_view(request):
    html = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PayPi-Bridge</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            margin: 0;
            padding: 2rem;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            min-height: 100vh;
            color: #e2e8f0;
        }
        .container { max-width: 900px; margin: 0 auto; }
        h1 {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
            background: linear-gradient(90deg, #38bdf8, #a78bfa, #FF9800);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            -webkit-text-stroke: 1px #FF9800;
            paint-order: stroke fill;
        }
        .subtitle { color: #94a3b8; margin-bottom: 2rem; font-size: 0.95rem; }
        .card {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(71, 85, 105, 0.5);
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
        }
        .card h2 {
            font-size: 1rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin: 0 0 0.75rem 0;
        }
        .card a {
            display: inline-block;
            color: #38bdf8;
            text-decoration: none;
            padding: 0.4rem 0;
            margin-right: 1rem;
            margin-bottom: 0.25rem;
        }
        .card a:hover { color: #7dd3fc; text-decoration: underline; }
        .links { display: flex; flex-wrap: wrap; gap: 0.5rem; }
        .badge {
            display: inline-block;
            background: rgba(56, 189, 248, 0.2);
            color: #38bdf8;
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
            font-size: 0.8rem;
            margin-left: 0.5rem;
        }
        .footer { margin-top: 2rem; color: #64748b; font-size: 0.85rem; }
        .logo-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
        .logo-header img { height: 48px; width: auto; display: block; }
        .user-header {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(71, 85, 105, 0.5);
            border-radius: 12px;
            padding: 1rem 1.5rem;
            margin-bottom: 1.5rem;
            display: none;
        }
        .user-header.active { display: block; }
        .user-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }
        .user-details {
            display: flex;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }
        .user-avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: linear-gradient(135deg, #38bdf8, #a78bfa);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            font-weight: 700;
            color: #0f172a;
        }
        .user-text {
            display: flex;
            flex-direction: column;
        }
        .user-name {
            font-weight: 600;
            color: #e2e8f0;
            font-size: 1rem;
        }
        .user-email {
            color: #94a3b8;
            font-size: 0.875rem;
        }
        .btn-logout {
            background: #ef4444;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
        }
        .btn-logout:hover { background: #dc2626; }
        .auth-prompt {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.3);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            text-align: center;
        }
        .auth-prompt.hidden { display: none; }
        .stats-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .stat-item {
            background: rgba(15, 23, 42, 0.5);
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #38bdf8;
            margin-bottom: 0.25rem;
        }
        .stat-label {
            font-size: 0.75rem;
            color: #94a3b8;
            text-transform: uppercase;
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="logo-header">
            <img src="/static/paypibridge/img/logo.png" alt="PayPi-Bridge" class="logo">
        </header>

        <!-- User Info Header (mostrado quando autenticado) -->
        <div class="user-header" id="user-header">
            <div class="user-info">
                <div class="user-details">
                    <div class="user-avatar" id="user-avatar">U</div>
                    <div class="user-text">
                        <div class="user-name" id="user-name">Carregando...</div>
                        <div class="user-email" id="user-email">-</div>
                    </div>
                </div>
                <button class="btn-logout" onclick="logout()">Sair</button>
            </div>
            <div class="stats-row" id="stats-row" style="margin-top: 1rem;">
                <div class="stat-item">
                    <div class="stat-value" id="stat-intents">-</div>
                    <div class="stat-label">Payment Intents</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="stat-consents">-</div>
                    <div class="stat-label">Consents</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="stat-payouts">-</div>
                    <div class="stat-label">Payouts</div>
                </div>
            </div>
        </div>

        <!-- Prompt de autenticação (mostrado quando não autenticado) -->
        <div class="auth-prompt" id="auth-prompt">
            <p style="margin: 0; color: #94a3b8;">
                👋 Bem-vindo! <a href="/forms/#auth-login" style="color: #22c55e; text-decoration: none; font-weight: 600;">Faça login</a> ou 
                <a href="/forms/#auth-register" style="color: #22c55e; text-decoration: none; font-weight: 600;">crie uma conta</a> para acessar seu dashboard.
            </p>
        </div>

        <div class="card" style="border-left: 3px solid #22c55e;">
            <h2 style="color: #22c55e;">🔐 Autenticação</h2>
            <div class="links">
                <a href="/forms/#auth-login">Login</a>
                <a href="/forms/#auth-register">Registro</a>
                <a href="/api/auth/me" id="link-profile" style="display:none;">Meu Perfil</a>
                <a href="/api/auth/check">Verificar Auth</a>
            </div>
        </div>

        <div class="card">
            <h2>Status e documentação</h2>
            <div class="links">
                <a href="/health/">Health</a>
                <a href="/forms/">Formulários de teste</a>
                <a href="/api/schema/swagger-ui/">Swagger UI</a>
                <a href="/api/schema/redoc/">ReDoc</a>
                <a href="/api/schema/">OpenAPI JSON</a>
            </div>
        </div>

        <div class="card">
            <h2>PaymentIntent e checkout</h2>
            <div class="links">
                <a href="/api/checkout/pi-intent">POST checkout/pi-intent</a>
                <a href="/api/intents">GET intents</a>
                <a href="/api/payments/verify">POST payments/verify</a>
            </div>
        </div>

        <div class="card pi">
            <h2>Pi Network</h2>
            <div class="links">
                <a href="/api/pi/status">GET pi/status</a>
                <a href="/api/pi/balance">GET pi/balance</a>
            </div>
        </div>

        <div class="card">
            <h2>Open Finance</h2>
            <div class="links">
                <a href="/api/consents">Consents</a>
                <a href="/api/bank-accounts/link">Link bank account</a>
                <a href="/api/payouts/pix">Payouts Pix</a>
                <a href="/api/reconcile">Reconcile</a>
            </div>
        </div>

        <div class="card">
            <h2>Webhooks</h2>
            <div class="links">
                <a href="/api/webhooks/ccip">POST webhooks/ccip</a>
            </div>
        </div>

        <p class="footer">PayPi-Bridge · Django + DRF · Pi Network & Open Finance</p>
    </div>
    <script>
        function getAccessToken() {
            return localStorage.getItem('access_token') || null;
        }

        function logout() {
            var refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
                fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh: refreshToken })
                }).catch(function() {});
            }
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.reload();
        }

        function loadUserDashboard() {
            var token = getAccessToken();
            if (!token) {
                // Não autenticado - mostrar prompt de login
                document.getElementById('auth-prompt').classList.remove('hidden');
                return;
            }

            // Usuário autenticado - carregar informações
            fetch('/api/auth/me', {
                headers: {
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                }
            })
            .then(function(r) {
                if (r.status === 401) {
                    // Token inválido ou expirado
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    document.getElementById('auth-prompt').classList.remove('hidden');
                    return null;
                }
                return r.json();
            })
            .then(function(data) {
                if (!data) return;

                var user = data.user || data;
                var userHeader = document.getElementById('user-header');
                var authPrompt = document.getElementById('auth-prompt');
                var linkProfile = document.getElementById('link-profile');

                // Mostrar header do usuário
                userHeader.classList.add('active');
                authPrompt.classList.add('hidden');
                linkProfile.style.display = 'inline-block';

                // Preencher informações do usuário
                var username = user.username || 'Usuário';
                var email = user.email || '-';
                var firstName = user.first_name || '';
                var lastName = user.last_name || '';

                document.getElementById('user-name').textContent = 
                    (firstName || lastName) ? (firstName + ' ' + lastName).trim() : username;
                document.getElementById('user-email').textContent = email;
                
                // Avatar com primeira letra
                var avatar = document.getElementById('user-avatar');
                avatar.textContent = username.charAt(0).toUpperCase();

                // Carregar estatísticas (placeholder por enquanto)
                // TODO: Implementar endpoints para buscar estatísticas reais
                document.getElementById('stat-intents').textContent = '-';
                document.getElementById('stat-consents').textContent = '-';
                document.getElementById('stat-payouts').textContent = '-';
            })
            .catch(function(e) {
                console.error('Erro ao carregar dashboard:', e);
                document.getElementById('auth-prompt').classList.remove('hidden');
            });
        }

        // Carregar dashboard ao carregar a página
        loadUserDashboard();
    </script>
</body>
</html>
"""
    return HttpResponse(html)


FORMS_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Formulários de teste · PayPi-Bridge</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            margin: 0;
            padding: 2rem;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            min-height: 100vh;
            color: #e2e8f0;
        }
        .container { max-width: 700px; margin: 0 auto; }
        h1 { font-size: 1.75rem; margin-bottom: 0.25rem; }
        .subtitle { color: #94a3b8; margin-bottom: 1.5rem; font-size: 0.9rem; }
        .back { color: #FF9800; text-decoration: none; margin-bottom: 1.5rem; display: inline-block; }
        .back:hover { color: #FFB74D; text-decoration: underline; }
        .card {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(71, 85, 105, 0.5);
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1.25rem;
        }
        .card h2 {
            font-size: 0.95rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin: 0 0 1rem 0;
        }
        .form-group { margin-bottom: 0.75rem; }
        .form-group label {
            display: block;
            color: #cbd5e1;
            font-size: 0.85rem;
            margin-bottom: 0.25rem;
        }
        .form-group input, .form-group textarea {
            width: 100%;
            padding: 0.5rem 0.75rem;
            border: 1px solid #475569;
            border-radius: 6px;
            background: #1e293b;
            color: #e2e8f0;
            font-size: 0.9rem;
        }
        .form-group textarea { min-height: 60px; resize: vertical; }
        .btn {
            background: #38bdf8;
            color: #0f172a;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
        }
        .btn:hover { background: #7dd3fc; }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .btn-pi { background: #FF9800; color: #0f172a; }
        .btn-pi:hover { background: #FFB74D; }
        .card.pi { border-left: 3px solid #FF9800; }
        .card.pi h2 { color: #FFB74D; }
        .result {
            margin-top: 1rem;
            padding: 0.75rem;
            background: #0f172a;
            border-radius: 6px;
            font-family: monospace;
            font-size: 0.8rem;
            white-space: pre-wrap;
            word-break: break-all;
            max-height: 200px;
            overflow-y: auto;
        }
        .result.ok { border-left: 3px solid #22c55e; }
        .result.err { border-left: 3px solid #ef4444; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back">← Voltar</a>
        <h1>Formulários de teste</h1>
        <p class="subtitle">Consultas à API PayPi-Bridge</p>

        <div class="card" id="auth-login" style="border-left: 3px solid #22c55e;">
            <h2 style="color: #22c55e;">🔐 Login (POST /api/auth/login)</h2>
            <form id="form-login">
                <div class="form-group">
                    <label>Username ou Email</label>
                    <input type="text" name="username" placeholder="usuario123 ou usuario@example.com" required>
                </div>
                <div class="form-group">
                    <label>Senha</label>
                    <input type="password" name="password" placeholder="Sua senha" required>
                </div>
                <button type="submit" class="btn" style="background: #22c55e;">Fazer Login</button>
            </form>
            <div id="result-login" class="result" style="display:none;"></div>
        </div>

        <div class="card" id="auth-register" style="border-left: 3px solid #22c55e;">
            <h2 style="color: #22c55e;">📝 Registro (POST /api/auth/register)</h2>
            <form id="form-register">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" name="username" placeholder="usuario123" required>
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email" placeholder="usuario@example.com" required>
                </div>
                <div class="form-group">
                    <label>Senha</label>
                    <input type="password" name="password" placeholder="Senha forte" required>
                </div>
                <div class="form-group">
                    <label>Confirmar Senha</label>
                    <input type="password" name="password_confirm" placeholder="Confirme a senha" required>
                </div>
                <div class="form-group">
                    <label>Nome (opcional)</label>
                    <input type="text" name="first_name" placeholder="João">
                </div>
                <div class="form-group">
                    <label>Sobrenome (opcional)</label>
                    <input type="text" name="last_name" placeholder="Silva">
                </div>
                <button type="submit" class="btn" style="background: #22c55e;">Criar Conta</button>
            </form>
            <div id="result-register" class="result" style="display:none;"></div>
        </div>

        <div class="card" id="auth-profile" style="border-left: 3px solid #22c55e;">
            <h2 style="color: #22c55e;">👤 Meu Perfil (GET /api/auth/me)</h2>
            <button type="button" class="btn" id="btn-profile" style="background: #22c55e;">Carregar Perfil</button>
            <div id="result-profile" class="result" style="display:none;"></div>
        </div>

        <div class="card pi">
            <h2>Status Pi (GET /api/pi/status)</h2>
            <button type="button" class="btn btn-pi" id="btn-status">Consultar status</button>
            <div id="result-status" class="result" style="display:none;"></div>
        </div>

        <div class="card pi">
            <h2>Saldo Pi (GET /api/pi/balance)</h2>
            <button type="button" class="btn btn-pi" id="btn-balance">Consultar saldo</button>
            <div id="result-balance" class="result" style="display:none;"></div>
        </div>

        <div class="card">
            <h2>Criar PaymentIntent (POST /api/checkout/pi-intent)</h2>
            <form id="form-intent">
                <div class="form-group">
                    <label>payee_user_id</label>
                    <input type="number" name="payee_user_id" value="1" required>
                </div>
                <div class="form-group">
                    <label>amount_pi</label>
                    <input type="text" name="amount_pi" value="10.5" placeholder="ex: 10.5" required>
                </div>
                <div class="form-group">
                    <label>metadata (JSON, opcional)</label>
                    <textarea name="metadata" placeholder='{"order_id": "123"}'>{"order_id": ""}</textarea>
                </div>
                <button type="submit" class="btn">Criar intent</button>
            </form>
            <div id="result-intent" class="result" style="display:none;"></div>
        </div>

        <div class="card pi">
            <h2>Verificar pagamento Pi (POST /api/payments/verify)</h2>
            <form id="form-verify">
                <div class="form-group">
                    <label>payment_id</label>
                    <input type="text" name="payment_id" placeholder="ID do pagamento Pi" required>
                </div>
                <div class="form-group">
                    <label>intent_id</label>
                    <input type="text" name="intent_id" placeholder="ex: pi_1234567890" required>
                </div>
                <button type="submit" class="btn btn-pi">Verificar</button>
            </form>
            <div id="result-verify" class="result" style="display:none;"></div>
        </div>
    </div>
    <script>
        function getCookie(name) {
            var v = document.cookie.match('(^|;) ?' + name + '=([^;]*)');
            return v ? v[2] : null;
        }
        function showResult(el, text, isOk) {
            el.textContent = text;
            el.className = 'result ' + (isOk ? 'ok' : 'err');
            el.style.display = 'block';
        }
        document.getElementById('btn-status').onclick = function() {
            var el = document.getElementById('result-status');
            el.style.display = 'block';
            el.textContent = 'Carregando...';
            fetch('/api/pi/status')
                .then(function(r) { return r.json().then(function(j) { return [r.status, j]; }); })
                .then(function(arr) {
                    var status = arr[0], j = arr[1];
                    showResult(el, JSON.stringify(j, null, 2), status >= 200 && status < 300);
                })
                .catch(function(e) { showResult(el, 'Erro: ' + e.message, false); });
        };
        document.getElementById('btn-balance').onclick = function() {
            var el = document.getElementById('result-balance');
            el.style.display = 'block';
            el.textContent = 'Carregando...';
            fetch('/api/pi/balance')
                .then(function(r) { return r.json().then(function(j) { return [r.status, j]; }); })
                .then(function(arr) {
                    var status = arr[0], j = arr[1];
                    showResult(el, JSON.stringify(j, null, 2), status >= 200 && status < 300);
                })
                .catch(function(e) { showResult(el, 'Erro: ' + e.message, false); });
        };
        document.getElementById('form-intent').onsubmit = function(e) {
            e.preventDefault();
            var el = document.getElementById('result-intent');
            var fd = new FormData(this);
            var meta = fd.get('metadata');
            var metaObj = {};
            try { metaObj = meta ? JSON.parse(meta) : {}; } catch(err) { metaObj = {}; }
            var body = {
                payee_user_id: parseInt(fd.get('payee_user_id'), 10),
                amount_pi: fd.get('amount_pi'),
                metadata: metaObj
            };
            el.style.display = 'block';
            el.textContent = 'Enviando...';
            var csrf = getCookie('csrftoken');
            fetch('/api/checkout/pi-intent', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf || '' },
                body: JSON.stringify(body),
                credentials: 'same-origin'
            })
                .then(function(r) { return r.json().then(function(j) { return [r.status, j]; }); })
                .then(function(arr) {
                    var status = arr[0], j = arr[1];
                    var text = status === 201 && j.intent_id
                        ? 'Intent criado. intent_id: ' + j.intent_id + '\n\n' + JSON.stringify(j, null, 2)
                        : JSON.stringify(j, null, 2);
                    showResult(el, text, status >= 200 && status < 300);
                })
                .catch(function(e) { showResult(el, 'Erro: ' + e.message, false); });
        };
        document.getElementById('form-verify').onsubmit = function(e) {
            e.preventDefault();
            var el = document.getElementById('result-verify');
            var fd = new FormData(this);
            var body = { payment_id: fd.get('payment_id'), intent_id: fd.get('intent_id') };
            el.style.display = 'block';
            el.textContent = 'Enviando...';
            var csrf = getCookie('csrftoken');
            fetch('/api/payments/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf || '' },
                body: JSON.stringify(body),
                credentials: 'same-origin'
            })
                .then(function(r) { return r.json().then(function(j) { return [r.status, j]; }); })
                .then(function(arr) {
                    var status = arr[0], j = arr[1];
                    showResult(el, JSON.stringify(j, null, 2), status >= 200 && status < 300);
                })
                .catch(function(e) { showResult(el, 'Erro: ' + e.message, false); });
        };

        // Login form handler
        document.getElementById('form-login').onsubmit = function(e) {
            e.preventDefault();
            var el = document.getElementById('result-login');
            var fd = new FormData(this);
            var body = {
                username: fd.get('username'),
                password: fd.get('password')
            };
            el.style.display = 'block';
            el.textContent = 'Fazendo login...';
            fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            })
                .then(function(r) { return r.json().then(function(j) { return [r.status, j]; }); })
                .then(function(arr) {
                    var status = arr[0], j = arr[1];
                    if (status === 200 && j.tokens) {
                        // Salvar tokens no localStorage
                        localStorage.setItem('access_token', j.tokens.access);
                        localStorage.setItem('refresh_token', j.tokens.refresh);
                        showResult(el, 'Login realizado com sucesso! Redirecionando...', true);
                        // Redirecionar para dashboard após 1 segundo
                        setTimeout(function() {
                            window.location.href = '/dashboard/';
                        }, 1000);
                    } else {
                        showResult(el, JSON.stringify(j, null, 2), false);
                    }
                })
                .catch(function(e) { showResult(el, 'Erro: ' + e.message, false); });
        };

        // Register form handler
        document.getElementById('form-register').onsubmit = function(e) {
            e.preventDefault();
            var el = document.getElementById('result-register');
            var fd = new FormData(this);
            if (fd.get('password') !== fd.get('password_confirm')) {
                showResult(el, 'As senhas não coincidem!', false);
                return;
            }
            var body = {
                username: fd.get('username'),
                email: fd.get('email'),
                password: fd.get('password'),
                password_confirm: fd.get('password_confirm'),
                first_name: fd.get('first_name') || '',
                last_name: fd.get('last_name') || ''
            };
            el.style.display = 'block';
            el.textContent = 'Criando conta...';
            fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            })
                .then(function(r) { return r.json().then(function(j) { return [r.status, j]; }); })
                .then(function(arr) {
                    var status = arr[0], j = arr[1];
                    if (status === 201 && j.tokens) {
                        // Salvar tokens no localStorage
                        localStorage.setItem('access_token', j.tokens.access);
                        localStorage.setItem('refresh_token', j.tokens.refresh);
                        showResult(el, 'Conta criada com sucesso! Redirecionando...', true);
                        // Redirecionar para página inicial (dashboard) após 1 segundo
                        setTimeout(function() {
                            window.location.href = '/';
                        }, 1000);
                    } else {
                        showResult(el, JSON.stringify(j, null, 2), false);
                    }
                })
                .catch(function(e) { showResult(el, 'Erro: ' + e.message, false); });
        };

        // Profile button handler
        document.getElementById('btn-profile').onclick = function() {
            var el = document.getElementById('result-profile');
            var token = localStorage.getItem('access_token');
            if (!token) {
                showResult(el, 'Erro: Não autenticado. Faça login primeiro.', false);
                return;
            }
            el.style.display = 'block';
            el.textContent = 'Carregando...';
            fetch('/api/auth/me', {
                headers: {
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                }
            })
                .then(function(r) { return r.json().then(function(j) { return [r.status, j]; }); })
                .then(function(arr) {
                    var status = arr[0], j = arr[1];
                    if (status === 401) {
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('refresh_token');
                        showResult(el, 'Sessão expirada. Faça login novamente.', false);
                    } else {
                        showResult(el, JSON.stringify(j, null, 2), status >= 200 && status < 300);
                    }
                })
                .catch(function(e) { showResult(el, 'Erro: ' + e.message, false); });
        };
    </script>
</body>
</html>
"""


@ensure_csrf_cookie
def forms_view(request):
    return HttpResponse(FORMS_HTML)


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - PayPi-Bridge</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            margin: 0;
            padding: 2rem;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            min-height: 100vh;
            color: #e2e8f0;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(71, 85, 105, 0.5);
        }
        h1 {
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
            background: linear-gradient(90deg, #38bdf8, #a78bfa, #FF9800);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .btn {
            background: #38bdf8;
            color: #0f172a;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover { background: #7dd3fc; }
        .btn-danger {
            background: #ef4444;
            color: white;
        }
        .btn-danger:hover { background: #dc2626; }
        .card {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(71, 85, 105, 0.5);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .card h2 {
            margin-top: 0;
            color: #38bdf8;
            font-size: 1.25rem;
        }
        .user-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .info-item {
            padding: 0.75rem;
            background: rgba(15, 23, 42, 0.5);
            border-radius: 6px;
        }
        .info-label {
            font-size: 0.75rem;
            color: #94a3b8;
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }
        .info-value {
            font-size: 1rem;
            font-weight: 600;
            color: #e2e8f0;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .stat-card {
            background: rgba(15, 23, 42, 0.5);
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #38bdf8;
            margin-bottom: 0.25rem;
        }
        .stat-label {
            font-size: 0.875rem;
            color: #94a3b8;
        }
        .loading {
            text-align: center;
            padding: 2rem;
            color: #94a3b8;
        }
        .error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid #ef4444;
            color: #fca5a5;
            padding: 1rem;
            border-radius: 6px;
            margin-bottom: 1rem;
        }
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .action-btn {
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid rgba(71, 85, 105, 0.5);
            color: #e2e8f0;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            text-decoration: none;
            display: block;
            transition: all 0.2s;
        }
        .action-btn:hover {
            background: rgba(30, 41, 59, 0.8);
            border-color: #38bdf8;
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Dashboard</h1>
            <div>
                <a href="/forms/" class="btn" style="margin-right: 0.5rem;">Formulários</a>
                <button class="btn btn-danger" onclick="logout()">Sair</button>
            </div>
        </div>

        <div id="loading" class="loading">Carregando informações do usuário...</div>
        <div id="error" class="error" style="display:none;"></div>
        <div id="dashboard" style="display:none;">
            <div class="card">
                <h2>👤 Informações do Usuário</h2>
                <div class="user-info" id="user-info"></div>
            </div>

            <div class="card">
                <h2>📈 Estatísticas</h2>
                <div class="stats-grid" id="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="stat-intents">-</div>
                        <div class="stat-label">Payment Intents</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="stat-consents">-</div>
                        <div class="stat-label">Consents</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="stat-payouts">-</div>
                        <div class="stat-label">Payouts</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>⚡ Ações Rápidas</h2>
                <div class="quick-actions">
                    <a href="/forms/#auth-profile" class="action-btn">
                        <strong>👤 Meu Perfil</strong><br>
                        <small>Ver e editar perfil</small>
                    </a>
                    <a href="/forms/#form-intent" class="action-btn">
                        <strong>💰 Criar Payment Intent</strong><br>
                        <small>Criar novo intent de pagamento</small>
                    </a>
                    <a href="/forms/#auth-register" class="action-btn">
                        <strong>🔐 Gerenciar Conta</strong><br>
                        <small>Alterar senha e configurações</small>
                    </a>
                    <a href="/api/schema/swagger-ui/" class="action-btn">
                        <strong>📚 API Docs</strong><br>
                        <small>Documentação da API</small>
                    </a>
                </div>
            </div>
        </div>
    </div>

    <script>
        function getCookie(name) {
            var v = document.cookie.match('(^|;) ?' + name + '=([^;]*)');
            return v ? v[2] : null;
        }

        function getAccessToken() {
            return localStorage.getItem('access_token') || null;
        }

        function logout() {
            var refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
                fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh: refreshToken })
                }).catch(function() {});
            }
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/forms/#auth-login';
        }

        function loadUserProfile() {
            var token = getAccessToken();
            if (!token) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').style.display = 'block';
                document.getElementById('error').textContent = 'Não autenticado. Redirecionando para login...';
                setTimeout(function() {
                    window.location.href = '/forms/#auth-login';
                }, 2000);
                return;
            }

            fetch('/api/auth/me', {
                headers: {
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                }
            })
            .then(function(r) {
                if (r.status === 401) {
                    throw new Error('Token inválido ou expirado');
                }
                return r.json();
            })
            .then(function(data) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('dashboard').style.display = 'block';

                var user = data.user || data;
                var userInfo = document.getElementById('user-info');
                userInfo.innerHTML = 
                    '<div class="info-item"><div class="info-label">Username</div><div class="info-value">' + (user.username || '-') + '</div></div>' +
                    '<div class="info-item"><div class="info-label">Email</div><div class="info-value">' + (user.email || '-') + '</div></div>' +
                    '<div class="info-item"><div class="info-label">Nome</div><div class="info-value">' + (user.first_name || '-') + ' ' + (user.last_name || '') + '</div></div>' +
                    '<div class="info-item"><div class="info-label">ID</div><div class="info-value">' + (user.id || '-') + '</div></div>';

                // Carregar estatísticas (placeholder por enquanto)
                document.getElementById('stat-intents').textContent = '-';
                document.getElementById('stat-consents').textContent = '-';
                document.getElementById('stat-payouts').textContent = '-';
            })
            .catch(function(e) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').style.display = 'block';
                document.getElementById('error').textContent = 'Erro ao carregar perfil: ' + e.message + '. Redirecionando para login...';
                setTimeout(function() {
                    window.location.href = '/forms/#auth-login';
                }, 3000);
            });
        }

        // Carregar perfil ao carregar a página
        loadUserProfile();
    </script>
</body>
</html>
"""


@ensure_csrf_cookie
def dashboard_view(request):
    return HttpResponse(DASHBOARD_HTML)


urlpatterns = [
    path("", home_view),
    path("health/", health_view),
    path("forms/", forms_view),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/", include("app.paypibridge.urls")),
]
