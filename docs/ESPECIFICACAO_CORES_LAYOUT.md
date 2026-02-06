# Especificação de cores e layout – PayPi-Bridge

Documento de referência para manter cores e layout consistentes em todas as páginas e futuros frontends do projeto.

---

## 1. Paleta de cores

### 1.1 Cores principais (tema escuro)

| Nome           | Hex       | Uso |
|----------------|-----------|-----|
| **Background** | `#0f172a` | Fundo principal, gradiente; fundo de blocos de resultado |
| **Surface**    | `#1e293b` | Fundo de cards; fundo de inputs e textareas |
| **Border**     | `#475569` | Bordas de cards e inputs (com opacidade onde indicado) |
| **Border (card)** | `rgba(71, 85, 105, 0.5)` | Borda dos cards |

### 1.2 Texto

| Nome            | Hex       | Uso |
|-----------------|-----------|-----|
| **Texto principal** | `#e2e8f0` | Corpo do texto |
| **Texto secundário** | `#94a3b8` | Subtítulos, títulos de card (h2), descrições |
| **Texto em formulário** | `#cbd5e1` | Labels de formulário |
| **Rodapé**      | `#64748b` | Texto do footer |

### 1.3 Destaque e interação (azul / cyan)

| Nome        | Hex       | Uso |
|-------------|-----------|-----|
| **Primária** | `#38bdf8` | Links, botões, gradiente do título |
| **Hover**   | `#7dd3fc` | Links e botões em hover |
| **Badge/background** | `rgba(56, 189, 248, 0.2)` | Fundo de badges |

### 1.4 Laranja Pi (logo)

Tom de laranja alinhado ao logotipo da Pi Network (ex.: minepi.com/partners), para uso em elementos que remetem à Pi (logo, CTAs, destaques).

| Nome        | Hex       | Uso |
|-------------|-----------|-----|
| **Laranja Pi** | `#FF9800` | Logo, botões/links Pi, destaques de saldo/conversão Pi |
| **Laranja Pi (hover)** | `#FFB74D` | Hover em elementos com Laranja Pi |
| **Laranja Pi (background)** | `rgba(255, 152, 0, 0.2)` | Fundo de badges ou cards relacionados a Pi |

### 1.5 Gradiente do título

| Uso     | Valor |
|---------|--------|
| **Título h1** | `linear-gradient(90deg, #38bdf8, #a78bfa)` (azul → roxo) |
| **Título h1 (alternativa Pi)** | `linear-gradient(90deg, #FF9800, #a78bfa)` (laranja Pi → roxo) |

### 1.6 Fundo da página

| Uso     | Valor |
|---------|--------|
| **Body** | `linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)` |

### 1.7 Feedback (resultados / status)

| Nome    | Hex       | Uso |
|---------|-----------|-----|
| **Sucesso** | `#22c55e` | Borda esquerda do bloco de resultado (.result.ok) |
| **Erro**    | `#ef4444` | Borda esquerda do bloco de resultado (.result.err) |

### 1.8 Botão

| Estado  | Propriedade | Valor |
|---------|-------------|--------|
| Normal  | background  | `#38bdf8` |
| Normal  | color       | `#0f172a` |
| Hover   | background  | `#7dd3fc` |
| Disabled| opacity     | `0.6` |

**Botão com tema Pi (opcional):** background `#FF9800`, hover `#FFB74D`, color `#0f172a`.

---

## 2. Tipografia

| Elemento     | font-family | font-size | font-weight | Observação |
|--------------|-------------|-----------|-------------|------------|
| **body**     | `'Segoe UI', system-ui, sans-serif` | (herdado) | normal | Texto geral |
| **h1 (home)**| (igual body) | `2rem` | `700` | Com gradiente de cor |
| **h1 (forms)**| (igual body) | `1.75rem` | (normal) | Página de formulários |
| **h2 (card)**| (igual body) | `1rem` ou `0.95rem` | normal | Título da card, uppercase |
| **subtitle** | (igual body) | `0.95rem` ou `0.9rem` | normal | Cor secundária |
| **label**    | (igual body) | `0.85rem` | normal | Labels de formulário |
| **input/textarea** | (igual body) | `0.9rem` | normal | Campos de formulário |
| **btn**      | (igual body) | `0.9rem` | `600` | Botões |
| **result**   | `monospace` | `0.8rem` | normal | Bloco de resultado JSON |
| **badge**    | (igual body) | `0.8rem` | normal | Badges |
| **footer**   | (igual body) | `0.85rem` | normal | Rodapé |

**Card h2:** `text-transform: uppercase`, `letter-spacing: 0.05em`.

---

## 3. Espaçamento e layout

### 3.1 Container

| Página   | Classe     | max-width | margin   |
|----------|------------|-----------|----------|
| Home     | `.container` | `900px` | `0 auto` |
| Forms    | `.container` | `700px` | `0 auto` |

### 3.2 Body

- `margin: 0`
- `padding: 2rem`
- `min-height: 100vh`

### 3.3 Cards

| Propriedade | Valor |
|-------------|--------|
| background | `rgba(30, 41, 59, 0.8)` |
| border | `1px solid rgba(71, 85, 105, 0.5)` |
| border-radius | `12px` |
| padding | `1.25rem 1.5rem` |
| margin-bottom | `1rem` (home) ou `1.25rem` (forms) |

### 3.4 Card h2

- `margin: 0 0 0.75rem 0` (home) ou `0 0 1rem 0` (forms)

### 3.5 Links (dentro de card)

- `padding: 0.4rem 0`
- `margin-right: 1rem`
- `margin-bottom: 0.25rem`

### 3.6 Formulário

| Elemento    | margin-bottom |
|-------------|----------------|
| .form-group | `0.75rem` |
| .form-group label | `0.25rem` (entre label e input) |

### 3.7 Botão

- `padding: 0.5rem 1rem`
- `border-radius: 6px`

### 3.8 Input / textarea

- `padding: 0.5rem 0.75rem`
- `border-radius: 6px`
- `width: 100%`
- textarea: `min-height: 60px`, `resize: vertical`

### 3.9 Bloco de resultado (.result)

- `margin-top: 1rem`
- `padding: 0.75rem`
- `border-radius: 6px`
- `max-height: 200px`
- `overflow-y: auto`
- Borda de status: `border-left: 3px solid` (#22c55e ok, #ef4444 err)

### 3.10 Footer

- `margin-top: 2rem`

### 3.11 Badge

- `padding: 0.25rem 0.5rem`
- `border-radius: 6px`
- `margin-left: 0.5rem`

---

## 4. Componentes resumidos

### 4.1 Card

- Fundo surface semi-transparente, borda discreta, cantos 12px.
- Título em maiúsculas, cor secundária, letter-spacing.

### 4.2 Link

- Cor primária (#38bdf8), sem sublinhado; hover com sublinhado e cor #7dd3fc.

### 4.3 Botão (.btn)

- Fundo primário, texto escuro (#0f172a), peso 600, cursor pointer.
- Hover: fundo mais claro (#7dd3fc). Disabled: opacity 0.6.

### 4.4 Input / textarea

- Fundo #1e293b, borda #475569, texto #e2e8f0, border-radius 6px.

### 4.5 Resultado (.result)

- Fundo #0f172a, monospace, 0.8rem.
- .result.ok: borda esquerda verde (#22c55e).
- .result.err: borda esquerda vermelha (#ef4444).

---

## 5. Variáveis CSS (sugestão para implementação)

Para facilitar manutenção, pode-se usar variáveis no CSS:

```css
:root {
  /* Cores base */
  --color-bg: #0f172a;
  --color-surface: #1e293b;
  --color-border: #475569;
  --color-text: #e2e8f0;
  --color-text-muted: #94a3b8;
  --color-text-form-label: #cbd5e1;
  --color-footer: #64748b;
  /* Primária */
  --color-primary: #38bdf8;
  --color-primary-hover: #7dd3fc;
  --color-primary-bg: rgba(56, 189, 248, 0.2);
  /* Laranja Pi (logo) */
  --color-pi-orange: #FF9800;
  --color-pi-orange-hover: #FFB74D;
  --color-pi-orange-bg: rgba(255, 152, 0, 0.2);
  /* Gradiente título */
  --gradient-title: linear-gradient(90deg, #38bdf8, #a78bfa);
  --gradient-title-pi: linear-gradient(90deg, #FF9800, #a78bfa);
  /* Body */
  --gradient-body: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
  /* Feedback */
  --color-success: #22c55e;
  --color-error: #ef4444;
  /* Botão */
  --color-btn-text: #0f172a;
  /* Layout */
  --radius-sm: 6px;
  --radius-md: 12px;
  --font-sans: 'Segoe UI', system-ui, sans-serif;
}
```

---

## 6. Onde aplicar

- Página inicial (`/`)
- Página de formulários de teste (`/forms/`)
- Qualquer nova página HTML servida pelo backend PayPi-Bridge
- Futuros frontends (React, etc.) que queiram seguir a mesma identidade visual

**Última atualização:** conforme implementação em `backend/config/urls.py` (home_view e FORMS_HTML).
