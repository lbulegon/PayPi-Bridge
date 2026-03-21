from django.http import JsonResponse, HttpResponse
from django.urls import path, include
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from app.paypibridge.views import BridgeHealthView


def health_view(request):
    return JsonResponse({"status": "ok"})


def home_view(request):
    html = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PayPi-Bridge - Gateway Pi → BRL</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            min-height: 100vh;
            color: #e2e8f0;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .hero {
            text-align: center;
            padding: 4rem 2rem;
            margin-bottom: 4rem;
        }
        .hero-logo {
            height: 120px;
            width: auto;
            margin-bottom: 2rem;
        }
        h1 {
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: linear-gradient(90deg, #38bdf8, #a78bfa, #FF9800);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.2;
        }
        .hero-subtitle {
            font-size: 1.5rem;
            color: #94a3b8;
            margin-bottom: 2rem;
            font-weight: 300;
        }
        .hero-description {
            font-size: 1.125rem;
            color: #cbd5e1;
            max-width: 800px;
            margin: 0 auto 3rem;
            line-height: 1.8;
        }
        .cta-buttons {
            display: flex;
            gap: 1rem;
            justify-content: center;
            flex-wrap: wrap;
            margin-bottom: 4rem;
        }
        .btn-primary {
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white;
            padding: 1rem 2rem;
            border-radius: 12px;
            font-size: 1.125rem;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s;
            box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4);
        }
        .btn-secondary {
            background: rgba(30, 41, 59, 0.8);
            border: 2px solid #38bdf8;
            color: #38bdf8;
            padding: 1rem 2rem;
            border-radius: 12px;
            font-size: 1.125rem;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s;
        }
        .btn-secondary:hover {
            background: rgba(56, 189, 248, 0.1);
            transform: translateY(-2px);
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 4rem;
        }
        .feature-card {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(71, 85, 105, 0.5);
            border-radius: 16px;
            padding: 2rem;
            transition: all 0.3s;
        }
        .feature-card:hover {
            transform: translateY(-4px);
            border-color: #38bdf8;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        }
        .feature-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #e2e8f0;
            margin-bottom: 0.75rem;
        }
        .feature-description {
            color: #94a3b8;
            line-height: 1.6;
        }
        .how-it-works {
            background: rgba(30, 41, 59, 0.4);
            border-radius: 16px;
            padding: 3rem;
            margin-bottom: 4rem;
        }
        .how-it-works h2 {
            font-size: 2rem;
            font-weight: 700;
            color: #e2e8f0;
            margin-bottom: 2rem;
            text-align: center;
        }
        .steps {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 1.5rem;
        }
        @media (max-width: 1200px) {
            .steps {
                grid-template-columns: repeat(3, 1fr);
            }
        }
        @media (max-width: 768px) {
            .steps {
                grid-template-columns: 1fr;
            }
        }
        .step {
            text-align: center;
        }
        .step-number {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #38bdf8, #a78bfa);
            color: #0f172a;
            font-size: 1.5rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1rem;
        }
        .step-title {
            font-size: 1.125rem;
            font-weight: 600;
            color: #e2e8f0;
            margin-bottom: 0.5rem;
        }
        .step-description {
            color: #94a3b8;
            font-size: 0.9rem;
        }
        .footer {
            text-align: center;
            padding: 2rem;
            color: #64748b;
            font-size: 0.9rem;
            border-top: 1px solid rgba(71, 85, 105, 0.5);
            margin-top: 4rem;
        }
        .logo-header { 
            display: flex; 
            align-items: flex-end; 
            justify-content: space-between;
            gap: 1rem; 
            margin-bottom: 1.5rem; 
            flex-wrap: wrap; 
            min-height: 48px;
        }
        .logo-header img { 
            height: 48px; 
            width: auto; 
            display: block;
            align-self: flex-end;
        }
        .welcome-message {
            flex: 1;
            text-align: right;
            color: #94a3b8;
            font-size: 0.95rem;
            margin-left: auto;
            align-self: flex-end;
            padding-bottom: 0;
        }
        @media (max-width: 768px) {
            .welcome-message {
                text-align: left;
                width: 100%;
                margin-left: 0;
                margin-top: 0.5rem;
            }
        }
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
        <!-- Hero Section -->
        <section class="hero">
            <img src="/static/paypibridge/img/logo.png" alt="PayPi-Bridge" class="hero-logo">
            <p class="hero-description">
                Conecte pagamentos em <strong style="color: #FF9800;">Pi Network</strong> com o sistema bancário brasileiro através de <strong style="color: #38bdf8;">Open Finance</strong>. 
                Converta Pi em reais (BRL) de forma segura, rápida e automatizada, com confirmação via blockchain e liquidação bancária instantânea.
            </p>
            <div class="cta-buttons">
                <a href="/login/" class="btn-primary">Entrar no Dashboard</a>
                <a href="/register/" class="btn-secondary">Criar Conta</a>
            </div>
        </section>

        <!-- Features Section -->
        <section class="features">
            <div class="feature-card">
                <div class="feature-icon">🔗</div>
                <h3 class="feature-title">Integração Pi Network</h3>
                <p class="feature-description">
                    Conecte-se diretamente com a Pi Network para receber pagamentos em Pi, 
                    verificando transações e saldos em tempo real.
                </p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🏦</div>
                <h3 class="feature-title">Open Finance</h3>
                <p class="feature-description">
                    Integração completa com Open Finance brasileiro para realizar pagamentos Pix, 
                    vincular contas bancárias e reconciliar transações automaticamente.
                </p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">⛓️</div>
                <h3 class="feature-title">Blockchain Soroban</h3>
                <p class="feature-description">
                    Confirmação de pagamentos via contratos inteligentes na blockchain Soroban, 
                    garantindo transparência e segurança nas transações.
                </p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <h3 class="feature-title">Liquidação Instantânea</h3>
                <p class="feature-description">
                    Conversão automática de Pi para BRL com liquidação bancária via Pix, 
                    permitindo recebimentos instantâneos em sua conta.
                </p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🔐</div>
                <h3 class="feature-title">Segurança Total</h3>
                <p class="feature-description">
                    Autenticação JWT, webhooks assinados com HMAC, idempotência e auditoria completa 
                    de todas as transações para máxima segurança.
                </p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3 class="feature-title">API Completa</h3>
                <p class="feature-description">
                    API RESTful completa com documentação OpenAPI/Swagger, 
                    permitindo integração fácil com qualquer aplicação.
                </p>
            </div>
        </section>

        <!-- How It Works Section -->
        <section class="how-it-works">
            <h2>Como Funciona</h2>
            <div class="steps">
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-title">Payment Intent</div>
                    <div class="step-description">
                        DApp cria um PaymentIntent on-chain no contrato Soroban e emite um evento
                    </div>
                </div>
                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-title">Webhook CCIP</div>
                    <div class="step-description">
                        Relayer (CCIP ou custom) envia webhook assinado para o backend
                    </div>
                </div>
                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-title">Validação</div>
                    <div class="step-description">
                        Backend valida o pagamento Pi e inicia processo de liquidação
                    </div>
                </div>
                <div class="step">
                    <div class="step-number">4</div>
                    <div class="step-title">Open Finance</div>
                    <div class="step-description">
                        Pagamento Pix é criado via Open Finance e enviado para sua conta bancária
                    </div>
                </div>
                <div class="step">
                    <div class="step-number">5</div>
                    <div class="step-title">Reconciliação</div>
                    <div class="step-description">
                        Sistema reconcilia automaticamente via API de transações bancárias
                    </div>
                </div>
            </div>
        </section>

        <!-- CTA Final -->
        <section style="text-align: center; margin-bottom: 4rem;">
            <h2 style="font-size: 2rem; color: #e2e8f0; margin-bottom: 1rem;">Pronto para começar?</h2>
            <p style="color: #94a3b8; font-size: 1.125rem; margin-bottom: 2rem;">
                Acesse seu dashboard e comece a converter Pi em BRL hoje mesmo
            </p>
            <div class="cta-buttons">
                <a href="/login/" class="btn-primary">Acessar Dashboard</a>
                <a href="/register/" class="btn-secondary">Criar Conta Grátis</a>
            </div>
        </section>

        <footer class="footer">
            <p>PayPi-Bridge · Gateway Pi → BRL · Django + DRF · Pi Network & Open Finance</p>
        </footer>
    </div>
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
            padding: 0;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            min-height: 100vh;
            color: #e2e8f0;
        }
        .forms-shell {
            display: grid;
            grid-template-columns: minmax(200px, 260px) 1fr;
            gap: 0;
            max-width: 1080px;
            margin: 0 auto;
            min-height: 100vh;
            padding: 1.25rem 1.25rem 2.5rem;
            align-items: start;
        }
        @media (max-width: 820px) {
            .forms-shell {
                grid-template-columns: 1fr;
                padding: 1rem;
            }
        }
        .forms-sidebar {
            position: sticky;
            top: 1rem;
            padding-right: 1rem;
            border-right: 1px solid rgba(71, 85, 105, 0.45);
        }
        @media (max-width: 820px) {
            .forms-sidebar {
                position: static;
                border-right: none;
                border-bottom: 1px solid rgba(71, 85, 105, 0.45);
                padding-right: 0;
                padding-bottom: 1rem;
                margin-bottom: 1rem;
            }
        }
        .sidebar-title {
            font-size: 1.35rem;
            margin: 0.35rem 0 0.2rem 0;
            font-weight: 700;
        }
        .sidebar-desc {
            color: #94a3b8;
            font-size: 0.8rem;
            margin: 0 0 1rem 0;
            line-height: 1.4;
        }
        .back {
            color: #FF9800;
            text-decoration: none;
            display: inline-block;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }
        .back:hover { color: #FFB74D; text-decoration: underline; }
        .forms-nav { display: flex; flex-direction: column; gap: 1rem; }
        .nav-section {
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }
        .nav-heading {
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #64748b;
            font-weight: 700;
            margin: 0;
        }
        .forms-nav a {
            display: block;
            padding: 0.45rem 0.65rem;
            border-radius: 8px;
            color: #cbd5e1;
            text-decoration: none;
            font-size: 0.875rem;
            border: 1px solid transparent;
            transition: background 0.15s, border-color 0.15s, color 0.15s;
        }
        .forms-nav a:hover {
            background: rgba(51, 65, 85, 0.5);
            color: #f1f5f9;
        }
        .forms-nav a.is-active {
            background: rgba(56, 189, 248, 0.12);
            border-color: rgba(56, 189, 248, 0.35);
            color: #7dd3fc;
        }
        @media (max-width: 820px) {
            .forms-nav {
                flex-direction: row;
                flex-wrap: wrap;
                gap: 0.35rem 0.5rem;
            }
            .nav-section {
                flex-direction: row;
                flex-wrap: wrap;
                align-items: center;
                gap: 0.25rem;
                width: 100%;
            }
            .nav-heading {
                width: 100%;
                margin-top: 0.5rem;
            }
            .nav-section:first-child .nav-heading { margin-top: 0; }
            .forms-nav a { padding: 0.35rem 0.55rem; font-size: 0.8rem; }
        }
        .forms-main {
            padding-left: 1.5rem;
            min-width: 0;
        }
        @media (max-width: 820px) {
            .forms-main { padding-left: 0; }
        }
        .form-panel { display: none; }
        .form-panel.is-active { display: block; animation: fadeIn 0.2s ease; }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .panel-blurb {
            color: #94a3b8;
            font-size: 0.88rem;
            margin: 0 0 1rem 0;
            line-height: 1.45;
        }
        .panel-blurb code {
            background: rgba(15, 23, 42, 0.9);
            padding: 0.1rem 0.35rem;
            border-radius: 4px;
            font-size: 0.8rem;
            color: #7dd3fc;
        }
        h1.page-fallback { display: none; }
        .card {
            background: rgba(30, 41, 59, 0.85);
            border: 1px solid rgba(71, 85, 105, 0.5);
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
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
        .card.auth { border-left: 3px solid #22c55e; }
        .card.auth h2 { color: #86efac; }
        .result {
            margin-top: 1rem;
            padding: 0.75rem;
            background: #0f172a;
            border-radius: 6px;
            font-family: monospace;
            font-size: 0.8rem;
            white-space: pre-wrap;
            word-break: break-all;
            max-height: 220px;
            overflow-y: auto;
        }
        .result.ok { border-left: 3px solid #22c55e; }
        .result.err { border-left: 3px solid #ef4444; }
    </style>
</head>
<body>
    <div class="forms-shell">
        <aside class="forms-sidebar">
            <a href="/" class="back">← Voltar</a>
            <h1 class="sidebar-title">Formulários</h1>
            <p class="sidebar-desc">Um painel por funcionalidade. Use o menu para alternar.</p>
            <nav class="forms-nav" aria-label="Funcionalidades">
                <div class="nav-section">
                    <span class="nav-heading">Conta</span>
                    <a href="/forms/#auth-login" data-panel="auth-login">Login</a>
                    <a href="/forms/#auth-register" data-panel="auth-register">Registro</a>
                    <a href="/forms/#auth-profile" data-panel="auth-profile">Meu perfil</a>
                </div>
                <div class="nav-section">
                    <span class="nav-heading">Pi</span>
                    <a href="/forms/#pi-status" data-panel="pi-status">Status</a>
                    <a href="/forms/#pi-balance" data-panel="pi-balance">Saldo</a>
                </div>
                <div class="nav-section">
                    <span class="nav-heading">Checkout</span>
                    <a href="/forms/#checkout-intent" data-panel="checkout-intent">Payment intent</a>
                </div>
                <div class="nav-section">
                    <span class="nav-heading">Pagamentos</span>
                    <a href="/forms/#section-verify" data-panel="section-verify">Verificar Pi</a>
                </div>
                <div class="nav-section">
                    <span class="nav-heading">Liquidação</span>
                    <a href="/forms/#section-settle" data-panel="section-settle">Pi → Pix</a>
                </div>
            </nav>
        </aside>
        <main class="forms-main">
            <div id="auth-login" class="form-panel is-active">
                <p class="panel-blurb">Autenticação e tokens JWT; após sucesso redireciona ao dashboard. Endpoint: <code>POST /api/auth/login</code></p>
                <div class="card auth">
                    <h2>Login</h2>
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
            </div>

            <div id="auth-register" class="form-panel">
                <p class="panel-blurb">Cria utilizador e devolve tokens. Endpoint: <code>POST /api/auth/register</code></p>
                <div class="card auth">
                    <h2>Registro</h2>
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
            </div>

            <div id="auth-profile" class="form-panel">
                <p class="panel-blurb">Requer token no armazenamento local (após login). Endpoint: <code>GET /api/auth/me</code></p>
                <div class="card auth">
                    <h2>Meu perfil</h2>
                    <button type="button" class="btn" id="btn-profile" style="background: #22c55e;">Carregar Perfil</button>
                    <div id="result-profile" class="result" style="display:none;"></div>
                </div>
            </div>

            <div id="pi-status" class="form-panel">
                <p class="panel-blurb">Estado do nó / serviço Pi integrado ao bridge. Endpoint: <code>GET /api/pi/status</code></p>
                <div class="card pi">
                    <h2>Status Pi</h2>
                    <button type="button" class="btn btn-pi" id="btn-status">Consultar status</button>
                    <div id="result-status" class="result" style="display:none;"></div>
                </div>
            </div>

            <div id="pi-balance" class="form-panel">
                <p class="panel-blurb">Consulta de saldo Pi. Endpoint: <code>GET /api/pi/balance</code></p>
                <div class="card pi">
                    <h2>Saldo Pi</h2>
                    <button type="button" class="btn btn-pi" id="btn-balance">Consultar saldo</button>
                    <div id="result-balance" class="result" style="display:none;"></div>
                </div>
            </div>

            <div id="checkout-intent" class="form-panel">
                <p class="panel-blurb">Inicia um pagamento em Pi para um payee. Endpoint: <code>POST /api/checkout/pi-intent</code></p>
                <div class="card">
                    <h2>Criar PaymentIntent</h2>
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
            </div>

            <div id="section-verify" class="form-panel">
                <p class="panel-blurb">Confirma pagamento Pi no intent (opcionalmente com txid no ledger). Endpoint: <code>POST /api/payments/verify</code></p>
                <div class="card pi">
                    <h2>Verificar pagamento Pi</h2>
                    <form id="form-verify">
                        <div class="form-group">
                            <label>payment_id</label>
                            <input type="text" name="payment_id" placeholder="ID do pagamento Pi" required>
                        </div>
                        <div class="form-group">
                            <label>intent_id</label>
                            <input type="text" name="intent_id" placeholder="ex: pi_1234567890" required>
                        </div>
                        <div class="form-group">
                            <label>txid (opcional, Horizon / ledger)</label>
                            <input type="text" name="txid" placeholder="hash da transação on-chain">
                        </div>
                        <button type="submit" class="btn btn-pi">Verificar</button>
                    </form>
                    <div id="result-verify" class="result" style="display:none;"></div>
                </div>
            </div>

            <div id="section-settle" class="form-panel">
                <p class="panel-blurb">Liquidação Pi → BRL → Pix. Requer Pi verificado e consent Open Finance do payee. Endpoint: <code>POST /api/settlements/execute</code></p>
                <div class="card auth">
                    <h2>Liquidação automática</h2>
                    <form id="form-settle">
                        <div class="form-group">
                            <label>intent_id</label>
                            <input type="text" name="intent_id" placeholder="ex: pi_1234567890" required>
                        </div>
                        <div class="form-group">
                            <label>CPF (só dígitos)</label>
                            <input type="text" name="cpf" placeholder="12345678901" maxlength="11" required>
                        </div>
                        <div class="form-group">
                            <label>Chave Pix</label>
                            <input type="text" name="pix_key" placeholder="email, telefone ou chave" required>
                        </div>
                        <div class="form-group">
                            <label>Descrição (opcional)</label>
                            <input type="text" name="description" placeholder="PayPi-Bridge">
                        </div>
                        <button type="submit" class="btn" style="background:#22c55e;color:#0f172a;">Liquidar (Pi→BRL→Pix)</button>
                    </form>
                    <div id="result-settle" class="result" style="display:none;"></div>
                </div>
            </div>
        </main>
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
        var LEGACY_PANEL = { 'form-intent': 'checkout-intent' };
        function resolvePanelIdFromHashFragment(frag) {
            var raw = (frag || '').replace(/^#/, '').trim();
            try {
                if (raw.indexOf('%') !== -1) raw = decodeURIComponent(raw);
            } catch (e) { /* manter raw */ }
            var id = LEGACY_PANEL[raw] || raw;
            return id;
        }
        function panelIdFromWindowHash() {
            return resolvePanelIdFromHashFragment(location.hash || '');
        }
        function validPanelOrLogin(id) {
            if (!id) return 'auth-login';
            var el = document.getElementById(id);
            if (!el || !el.classList.contains('form-panel')) return 'auth-login';
            return id;
        }
        function showPanel(panelId, opts) {
            opts = opts || {};
            var id = resolvePanelIdFromHashFragment(panelId);
            if (!id) id = 'auth-login';
            id = validPanelOrLogin(id);
            var target = document.getElementById(id);
            if (!target) return false;
            document.querySelectorAll('.form-panel').forEach(function(p) {
                p.classList.toggle('is-active', p.id === id);
            });
            document.querySelectorAll('.forms-nav a[data-panel]').forEach(function(a) {
                var ap = a.getAttribute('data-panel');
                a.classList.toggle('is-active', ap === id);
            });
            if (opts.updateHash !== false) {
                if (history.replaceState) {
                    history.replaceState(null, '', '#' + id);
                } else {
                    location.hash = id;
                }
            }
            return true;
        }
        function applyHashToPanel() {
            var id = validPanelOrLogin(panelIdFromWindowHash());
            showPanel(id, { updateHash: false });
        }
        function initFormsNav() {
            var links = document.querySelectorAll('.forms-nav a[data-panel]');
            links.forEach(function(a) {
                a.addEventListener('click', function(e) {
                    e.preventDefault();
                    showPanel(a.getAttribute('data-panel'));
                });
            });
            window.addEventListener('hashchange', function() {
                applyHashToPanel();
            });
            window.addEventListener('pageshow', function(ev) {
                if (ev.persisted) applyHashToPanel();
            });
            applyHashToPanel();
            window.addEventListener('load', function() {
                applyHashToPanel();
            });
            setTimeout(applyHashToPanel, 0);
        }
        function startFormsNavOnce() {
            if (window.__paypiFormsNavStarted) return;
            window.__paypiFormsNavStarted = true;
            initFormsNav();
        }
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', startFormsNavOnce);
        } else {
            startFormsNavOnce();
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
            var body = {
                payment_id: fd.get('payment_id'),
                intent_id: fd.get('intent_id'),
                txid: fd.get('txid') || ''
            };
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
        document.getElementById('form-settle').onsubmit = function(e) {
            e.preventDefault();
            var el = document.getElementById('result-settle');
            var fd = new FormData(this);
            var body = {
                intent_id: fd.get('intent_id'),
                cpf: fd.get('cpf'),
                pix_key: fd.get('pix_key'),
                description: fd.get('description') || ''
            };
            el.style.display = 'block';
            el.textContent = 'Liquidando...';
            var csrf = getCookie('csrftoken');
            fetch('/api/settlements/execute', {
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
                credentials: 'same-origin',
                body: JSON.stringify(body)
            })
                .then(function(r) { return r.json().then(function(j) { return [r.status, j]; }); })
                .then(function(arr) {
                    var status = arr[0], j = arr[1];
                    if (status === 200 && j.tokens) {
                        localStorage.setItem('access_token', j.tokens.access);
                        localStorage.setItem('refresh_token', j.tokens.refresh);
                        showResult(el, 'Login realizado com sucesso! Redirecionando...', true);
                        var url = j.redirect_url || '/dashboard/';
                        window.location.replace(url);
                    } else {
                        showResult(el, JSON.stringify(j, null, 2), false);
                    }
                })
                .catch(function(e) { showResult(el, 'Erro: ' + e.message, false); });
        };
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
                        localStorage.setItem('access_token', j.tokens.access);
                        localStorage.setItem('refresh_token', j.tokens.refresh);
                        showResult(el, 'Conta criada com sucesso! Redirecionando...', true);
                        setTimeout(function() {
                            window.location.href = '/';
                        }, 1000);
                    } else {
                        showResult(el, JSON.stringify(j, null, 2), false);
                    }
                })
                .catch(function(e) { showResult(el, 'Erro: ' + e.message, false); });
        };
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
        .card h2.section-title {
            font-size: 1rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin: 0 0 0.75rem 0;
        }
        .card .links {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        .card .links a {
            display: inline-block;
            color: #38bdf8;
            text-decoration: none;
            padding: 0.4rem 0;
            margin-right: 1rem;
            margin-bottom: 0.25rem;
        }
        .card .links a:hover { color: #7dd3fc; text-decoration: underline; }
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
        .services-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem 1.25rem;
            margin-top: 1rem;
            font-size: 0.85rem;
            color: #94a3b8;
        }
        .services-strip span strong { color: #e2e8f0; }
        .intent-table-wrap { overflow-x: auto; margin-top: 1rem; }
        .intent-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8rem;
        }
        .intent-table th, .intent-table td {
            padding: 0.5rem 0.6rem;
            text-align: left;
            border-bottom: 1px solid rgba(71, 85, 105, 0.4);
        }
        .intent-table th { color: #94a3b8; font-weight: 600; }
        .badge { display: inline-block; padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.7rem; }
        .badge-settled { background: rgba(34, 197, 94, 0.2); color: #86efac; }
        .badge-created { background: rgba(56, 189, 248, 0.15); color: #7dd3fc; }
        .badge-other { background: rgba(148, 163, 184, 0.2); color: #cbd5e1; }
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
                        <div class="stat-label">Payment Intents (total)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="stat-consents">-</div>
                        <div class="stat-label">Consents ativos</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="stat-payouts">-</div>
                        <div class="stat-label">Transações Pix</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="stat-settled">-</div>
                        <div class="stat-label">Liquidações (SETTLED)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="stat-pending-liq">-</div>
                        <div class="stat-label">Pi verificado → aguarda Pix</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="stat-liq-fail">-</div>
                        <div class="stat-label">Falhas de liquidação</div>
                    </div>
                </div>
                <div class="services-strip" id="services-strip">
                    <span><strong>Pi:</strong> <span id="svc-pi">—</span></span>
                    <span><strong>FX:</strong> <span id="svc-fx">—</span></span>
                    <span><strong>Relayer:</strong> <span id="svc-relayer">—</span></span>
                </div>
            </div>

            <div class="card">
                <h2>📋 Meus últimos Payment Intents</h2>
                <p style="color:#94a3b8;font-size:0.85rem;margin:0 0 0.5rem 0;">Filtrados pelo teu utilizador (JWT).</p>
                <div class="intent-table-wrap">
                    <table class="intent-table">
                        <thead>
                            <tr>
                                <th>intent_id</th>
                                <th>Status</th>
                                <th>Pi</th>
                                <th>Liquidação</th>
                                <th>Verificado</th>
                            </tr>
                        </thead>
                        <tbody id="recent-intents-body">
                            <tr><td colspan="5" style="color:#64748b;">A carregar…</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <h2>⚡ Ações Rápidas</h2>
                <div class="quick-actions">
                    <a href="/forms/#auth-profile" class="action-btn">
                        <strong>👤 Meu Perfil</strong><br>
                        <small>Ver e editar perfil</small>
                    </a>
                    <a href="/forms/#checkout-intent" class="action-btn">
                        <strong>💰 Criar Payment Intent</strong><br>
                        <small>Checkout Pi → BRL</small>
                    </a>
                    <a href="/forms/#section-verify" class="action-btn">
                        <strong>✓ Verificar pagamento Pi</strong><br>
                        <small>Ligar payment_id ao intent</small>
                    </a>
                    <a href="/forms/#section-settle" class="action-btn">
                        <strong>🏦 Liquidação Pix</strong><br>
                        <small>Pi verificado → BRL → Pix</small>
                    </a>
                    <a href="/forms/#auth-register" class="action-btn">
                        <strong>🔐 Gerenciar Conta</strong><br>
                        <small>Registo / senha</small>
                    </a>
                    <a href="/api/schema/swagger-ui/" target="_blank" rel="noopener" class="action-btn">
                        <strong>📚 API Docs</strong><br>
                        <small>Swagger / OpenAPI</small>
                    </a>
                    <a href="/health/bridge" target="_blank" rel="noopener" class="action-btn">
                        <strong>❤️ Health / Trust</strong><br>
                        <small>Pi + Horizon (modo confiança)</small>
                    </a>
                    <a href="/api/health" target="_blank" rel="noopener" class="action-btn">
                        <strong>🔧 Health completo</strong><br>
                        <small>Serviços e integrações</small>
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
            window.location.href = '/login/';
        }

        function loadDashboardStats(token) {
            fetch('/api/admin/stats', {
                headers: {
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                }
            })
            .then(function(r) { return r.json().then(function(j) { return [r.status, j]; }); })
            .then(function(arr) {
                var st = arr[0], s = arr[1];
                if (st < 200 || st >= 300 || !s.payment_intents) return;
                document.getElementById('stat-intents').textContent = s.payment_intents.total;
                document.getElementById('stat-consents').textContent = (s.consents.active != null ? s.consents.active : s.consents.total);
                document.getElementById('stat-payouts').textContent = s.pix_transactions.total;
                var setl = s.settlement || {};
                document.getElementById('stat-settled').textContent = setl.settled_intents != null ? setl.settled_intents : '0';
                document.getElementById('stat-pending-liq').textContent = setl.pending_liquidation != null ? setl.pending_liquidation : '0';
                document.getElementById('stat-liq-fail').textContent = setl.settlement_failed != null ? setl.settlement_failed : '0';
                var sv = s.services || {};
                document.getElementById('svc-pi').textContent = sv.pi_network && sv.pi_network.available ? 'OK' : 'indisponível';
                document.getElementById('svc-fx').textContent = (sv.fx_service && sv.fx_service.provider) ? sv.fx_service.provider : '—';
                var rs = sv.soroban_relayer || {};
                document.getElementById('svc-relayer').textContent = rs.enabled ? (rs.connected ? 'ligado' : 'configurado') : 'off';
            })
            .catch(function() {});
        }

        function intentStatusBadge(st) {
            if (st === 'SETTLED') return '<span class="badge badge-settled">' + st + '</span>';
            if (st === 'CREATED' || st === 'CONFIRMED') return '<span class="badge badge-created">' + st + '</span>';
            return '<span class="badge badge-other">' + (st || '-') + '</span>';
        }

        function loadRecentIntents(token) {
            var tbody = document.getElementById('recent-intents-body');
            fetch('/api/admin/intents?limit=8&mine=1', {
                headers: {
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                }
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                var rows = data.results || [];
                if (!rows.length) {
                    tbody.innerHTML = '<tr><td colspan="5" style="color:#64748b;">Nenhum intent ainda. Cria um em Formulários.</td></tr>';
                    return;
                }
                tbody.innerHTML = rows.map(function(it) {
                    var ver = it.verified_at ? 'sim' : '—';
                    var liq = it.settlement_status || (it.status === 'SETTLED' ? 'SETTLED' : '—');
                    return '<tr><td style="font-family:monospace;font-size:0.75rem;">' + (it.intent_id || '') + '</td><td>' +
                        intentStatusBadge(it.status) + '</td><td>' + (it.amount_pi || '-') + '</td><td>' + liq + '</td><td>' + ver + '</td></tr>';
                }).join('');
            })
            .catch(function() {
                tbody.innerHTML = '<tr><td colspan="5" style="color:#f87171;">Não foi possível carregar intents.</td></tr>';
            });
        }

        function loadUserProfile() {
            var token = getAccessToken();
            if (!token) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').style.display = 'block';
                document.getElementById('error').textContent = 'Não autenticado. Redirecionando para login...';
                setTimeout(function() {
                    window.location.href = '/login/';
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

                loadDashboardStats(token);
                loadRecentIntents(token);
            })
            .catch(function(e) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').style.display = 'block';
                document.getElementById('error').textContent = 'Erro ao carregar perfil: ' + e.message + '. Redirecionando para login...';
                setTimeout(function() {
                    window.location.href = '/login/';
                }, 3000);
            });
        }

        // Carregar perfil ao carregar a página
        loadUserProfile();
    </script>
</body>
</html>
"""


LOGIN_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - PayPi-Bridge</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            min-height: 100vh;
            color: #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            width: 100%;
            max-width: 420px;
            padding: 2rem;
        }
        .login-card {
            background: rgba(30, 41, 59, 0.9);
            border: 1px solid rgba(71, 85, 105, 0.5);
            border-radius: 16px;
            padding: 2.5rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
        }
        .logo-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo-header img {
            height: 64px;
            width: auto;
            margin-bottom: 1rem;
        }
        .logo-header h1 {
            font-size: 1.75rem;
            font-weight: 700;
            margin: 0;
            background: linear-gradient(90deg, #38bdf8, #a78bfa, #FF9800);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .form-group {
            margin-bottom: 1.25rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #cbd5e1;
            font-size: 0.9rem;
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid rgba(71, 85, 105, 0.5);
            border-radius: 8px;
            background: rgba(15, 23, 42, 0.5);
            color: #e2e8f0;
            font-size: 1rem;
            transition: all 0.2s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #38bdf8;
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.1);
        }
        .btn-login {
            width: 100%;
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white;
            border: none;
            padding: 0.875rem;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            margin-top: 0.5rem;
        }
        .btn-login:hover {
            background: linear-gradient(135deg, #16a34a, #15803d);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
        }
        .btn-login:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .error-message {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #fca5a5;
            padding: 0.75rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            display: none;
        }
        .error-message.show {
            display: block;
        }
        .register-link {
            text-align: center;
            margin-top: 1.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid rgba(71, 85, 105, 0.5);
        }
        .register-link a {
            color: #38bdf8;
            text-decoration: none;
            font-weight: 500;
        }
        .register-link a:hover {
            text-decoration: underline;
        }
        .back-link {
            position: absolute;
            top: 1rem;
            left: 1rem;
            color: #94a3b8;
            text-decoration: none;
            font-size: 0.9rem;
        }
        .back-link:hover {
            color: #e2e8f0;
        }
    </style>
</head>
<body>
    <a href="/" class="back-link">← Voltar</a>
    <div class="login-container">
        <div class="login-card">
            <div class="logo-header">
                <img src="/static/paypibridge/img/logo.png" alt="PayPi-Bridge">
                <h1>Login</h1>
            </div>
            
            <div class="error-message" id="error-message"></div>
            
            <form id="login-form">
                <div class="form-group">
                    <label for="username">Username ou Email</label>
                    <input type="text" id="username" name="username" placeholder="usuario123 ou usuario@example.com" required autofocus>
                </div>
                
                <div class="form-group">
                    <label for="password">Senha</label>
                    <input type="password" id="password" name="password" placeholder="Sua senha" required>
                </div>
                
                <button type="submit" class="btn-login" id="btn-login">
                    Entrar
                </button>
            </form>
            
            <div class="register-link">
                Não tem uma conta? <a href="/register/">Crie uma agora</a>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('login-form').onsubmit = function(e) {
            e.preventDefault();
            var btn = document.getElementById('btn-login');
            var errorDiv = document.getElementById('error-message');
            var username = document.getElementById('username').value;
            var password = document.getElementById('password').value;
            
            // Esconder erro anterior
            errorDiv.classList.remove('show');
            btn.disabled = true;
            btn.textContent = 'Entrando...';
            
            fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({ username: username, password: password })
            })
            .then(function(r) { return r.json().then(function(j) { return [r.status, j]; }); })
            .then(function(arr) {
                var status = arr[0], data = arr[1];
                
                if (status === 200 && data.tokens) {
                    // Salvar tokens
                    localStorage.setItem('access_token', data.tokens.access);
                    localStorage.setItem('refresh_token', data.tokens.refresh);
                    
                    // Redirecionar para dashboard (replace evita voltar para login com back)
                    var url = data.redirect_url || '/dashboard/';
                    window.location.replace(url);
                } else {
                    // Mostrar erro
                    errorDiv.textContent = data.message || data.detail || 'Erro ao fazer login';
                    errorDiv.classList.add('show');
                    btn.disabled = false;
                    btn.textContent = 'Entrar';
                }
            })
            .catch(function(e) {
                errorDiv.textContent = 'Erro de conexão: ' + e.message;
                errorDiv.classList.add('show');
                btn.disabled = false;
                btn.textContent = 'Entrar';
            });
        };
    </script>
</body>
</html>
"""


REGISTER_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registrar-se - PayPi-Bridge</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            min-height: 100vh;
            color: #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem 1rem;
        }
        .register-container {
            width: 100%;
            max-width: 480px;
        }
        .register-card {
            background: rgba(30, 41, 59, 0.9);
            border: 1px solid rgba(71, 85, 105, 0.5);
            border-radius: 16px;
            padding: 2.5rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
        }
        .logo-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo-header img {
            height: 64px;
            width: auto;
            margin-bottom: 1rem;
        }
        .logo-header h1 {
            font-size: 1.75rem;
            font-weight: 700;
            margin: 0;
            background: linear-gradient(90deg, #38bdf8, #a78bfa, #FF9800);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .form-group {
            margin-bottom: 1.25rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #cbd5e1;
            font-size: 0.9rem;
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid rgba(71, 85, 105, 0.5);
            border-radius: 8px;
            background: rgba(15, 23, 42, 0.5);
            color: #e2e8f0;
            font-size: 1rem;
            transition: all 0.2s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #38bdf8;
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.1);
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }
        .btn-register {
            width: 100%;
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white;
            border: none;
            padding: 0.875rem;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            margin-top: 0.5rem;
        }
        .btn-register:hover {
            background: linear-gradient(135deg, #16a34a, #15803d);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
        }
        .btn-register:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .error-message {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #fca5a5;
            padding: 0.75rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            display: none;
        }
        .error-message.show {
            display: block;
        }
        .login-link {
            text-align: center;
            margin-top: 1.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid rgba(71, 85, 105, 0.5);
        }
        .login-link a {
            color: #38bdf8;
            text-decoration: none;
            font-weight: 500;
        }
        .login-link a:hover {
            text-decoration: underline;
        }
        .back-link {
            position: absolute;
            top: 1rem;
            left: 1rem;
            color: #94a3b8;
            text-decoration: none;
            font-size: 0.9rem;
        }
        .back-link:hover {
            color: #e2e8f0;
        }
        @media (max-width: 640px) {
            .form-row {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <a href="/" class="back-link">← Voltar</a>
    <div class="register-container">
        <div class="register-card">
            <div class="logo-header">
                <img src="/static/paypibridge/img/logo.png" alt="PayPi-Bridge">
                <h1>Criar Conta</h1>
            </div>
            
            <div class="error-message" id="error-message"></div>
            
            <form id="register-form">
                <div class="form-group">
                    <label for="username">Username *</label>
                    <input type="text" id="username" name="username" placeholder="usuario123" required autofocus>
                </div>
                
                <div class="form-group">
                    <label for="email">Email *</label>
                    <input type="email" id="email" name="email" placeholder="usuario@example.com" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Senha *</label>
                    <input type="password" id="password" name="password" placeholder="Senha forte" required>
                </div>
                
                <div class="form-group">
                    <label for="password_confirm">Confirmar Senha *</label>
                    <input type="password" id="password_confirm" name="password_confirm" placeholder="Confirme a senha" required>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="first_name">Nome</label>
                        <input type="text" id="first_name" name="first_name" placeholder="João">
                    </div>
                    
                    <div class="form-group">
                        <label for="last_name">Sobrenome</label>
                        <input type="text" id="last_name" name="last_name" placeholder="Silva">
                    </div>
                </div>
                
                <button type="submit" class="btn-register" id="btn-register">
                    Criar Conta
                </button>
            </form>
            
            <div class="login-link">
                Já tem uma conta? <a href="/login/">Faça login</a>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('register-form').onsubmit = function(e) {
            e.preventDefault();
            var btn = document.getElementById('btn-register');
            var errorDiv = document.getElementById('error-message');
            var password = document.getElementById('password').value;
            var passwordConfirm = document.getElementById('password_confirm').value;
            
            // Validar senhas
            if (password !== passwordConfirm) {
                errorDiv.textContent = 'As senhas não coincidem!';
                errorDiv.classList.add('show');
                return;
            }
            
            // Esconder erro anterior
            errorDiv.classList.remove('show');
            btn.disabled = true;
            btn.textContent = 'Criando conta...';
            
            var formData = {
                username: document.getElementById('username').value,
                email: document.getElementById('email').value,
                password: password,
                password_confirm: passwordConfirm,
                first_name: document.getElementById('first_name').value || '',
                last_name: document.getElementById('last_name').value || ''
            };
            
            fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })
            .then(function(r) { return r.json().then(function(j) { return [r.status, j]; }); })
            .then(function(arr) {
                var status = arr[0], data = arr[1];
                
                if (status === 201 && data.tokens) {
                    // Salvar tokens
                    localStorage.setItem('access_token', data.tokens.access);
                    localStorage.setItem('refresh_token', data.tokens.refresh);
                    
                    // Redirecionar para dashboard
                    var url = data.redirect_url || '/dashboard/';
                    window.location.replace(url);
                } else {
                    // Mostrar erro
                    var errorMsg = data.message || data.detail || 'Erro ao criar conta';
                    if (data.username) errorMsg += '\\n' + data.username.join('\\n');
                    if (data.email) errorMsg += '\\n' + data.email.join('\\n');
                    if (data.password) errorMsg += '\\n' + data.password.join('\\n');
                    errorDiv.textContent = errorMsg;
                    errorDiv.classList.add('show');
                    btn.disabled = false;
                    btn.textContent = 'Criar Conta';
                }
            })
            .catch(function(e) {
                errorDiv.textContent = 'Erro de conexão: ' + e.message;
                errorDiv.classList.add('show');
                btn.disabled = false;
                btn.textContent = 'Criar Conta';
            });
        };
    </script>
</body>
</html>
"""


@ensure_csrf_cookie
def dashboard_view(request):
    return HttpResponse(DASHBOARD_HTML)


@ensure_csrf_cookie
def login_view(request):
    return HttpResponse(LOGIN_HTML)


@ensure_csrf_cookie
def register_view(request):
    return HttpResponse(REGISTER_HTML)


urlpatterns = [
    path("", home_view),
    path("health/", health_view),
    path("health/bridge", BridgeHealthView.as_view(), name="health-bridge"),
    path("forms/", forms_view),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/", include("app.paypibridge.urls")),
]
