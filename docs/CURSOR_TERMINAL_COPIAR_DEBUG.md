# Copiar saída do terminal para o chat (Cursor / VS Code)

## O que já está no projeto

O ficheiro **`.vscode/settings.json`** do PayPi-Bridge ativa:

| Opção | Efeito |
|--------|--------|
| `terminal.integrated.copyOnSelection` | Ao **selecionar** texto no terminal, a seleção vai **logo para a área de transferência**. Depois usa **Ctrl+V** no chat do Cursor para colar o debug. |
| `terminal.integrated.rightClickBehavior` | **Clique direito** no terminal: menu de copiar/colar mais previsível. |
| `terminal.integrated.scrollback` | Mais linhas no histórico para conseguires selecionar traces longos. |

Recarrega a janela se não notares efeito: **Ctrl+Shift+P** → `Developer: Reload Window`.

---

## Atalhos padrão (Windows)

- **Copiar** do terminal: **Ctrl+Shift+C** (ou: selecionar com `copyOnSelection` ativo → já fica copiado).
- **Colar** no terminal: **Ctrl+Shift+V**  
- **Ctrl+C** no terminal = interromper comando (não é “copiar”).

---

## Colar no terminal com Ctrl+V (opcional, no teu PC)

Isto não vai no repositório: no **Cursor** abre **File → Preferences → Keyboard Shortcuts** → ícone **{}** (abrir `keybindings.json`) e acrescenta:

```json
[
  {
    "key": "ctrl+v",
    "command": "workbench.action.terminal.paste",
    "when": "terminalFocus"
  }
]
```

Se o Ctrl+V passar a conflitar com o shell, remove esta entrada.

---

## Onde ficam as definições “globais” no Windows

- **Settings:** `%APPDATA%\Cursor\User\settings.json`  
- **Keybindings:** `%APPDATA%\Cursor\User\keybindings.json`  

As do **workspace** (`.vscode/settings.json`) aplicam-se quando abres esta pasta e podem somar-se às globais.
