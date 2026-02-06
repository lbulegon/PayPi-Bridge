# PayPi-Bridge como serviço no SinapUm

## Resposta direta

**Sim.** O PayPi-Bridge pode ser colocado como um **serviço** no ecossistema SinapUm, no mesmo padrão dos outros (OpenMind, MCP, iFood): um serviço com porta própria, chamado pelo Core_SinapUm ou pelos sistemas Source (Evora, Eventix, etc.) via HTTP/REST.

---

## Como os outros serviços estão no SinapUm

No Core_SinapUm os serviços estão assim:

| Serviço        | Porta | Tipo    | Descrição                          |
|----------------|-------|---------|------------------------------------|
| Django Core    | 5000  | Django  | Aplicação principal                |
| OpenMind AI    | 8001  | FastAPI | Análise de imagens e IA            |
| MCP Service    | 7010  | FastAPI | Gateway para tools (MCP)           |
| iFood Service  | 7020  | FastAPI | OAuth e sincronização iFood        |
| PayPi-Bridge   | *(hoje 9080 standalone)* | Django+DRF | Pi → BRL, checkout, webhook, Open Finance |

O PayPi-Bridge pode entrar nessa tabela como mais um serviço, com URL fixa e (opcional) API key, como já se faz com OpenMind e MCP.

---

## Duas formas de “estar no SinapUm”

### 1. Serviço no mesmo stack (docker-compose do SinapUm)

- O **Core_SinapUm** tem um `docker-compose.yml` (ex.: em `/root/Core_SinapUm/`) onde sobem Django Core, OpenMind, MCP, iFood, PostgreSQL, etc.
- Você adiciona o **PayPi-Bridge** como mais um serviço nesse mesmo compose:
  - Imagem/build do PayPi-Bridge (Django atual).
  - Porta dedicada, ex.: **7030** (ou outra livre).
  - Mesma rede interna que o Core e os outros serviços.
  - Variáveis de ambiente (Pi, Open Finance, CCIP, DB se for compartilhado ou próprio).
- Os outros sistemas (Evora, Eventix, etc.) e o próprio Core passam a chamar o PayPi-Bridge pela URL interna, ex.: `http://paypibridge:7030` (ou pelo host/IP + porta, ex.: `http://69.169.102.84:7030`).

**Vantagens:** um único lugar para subir/parar tudo; rede interna; fácil de documentar como “serviço SinapUm”.

**Desafio:** adaptar o `docker-compose.yml` e o `Dockerfile` do PayPi-Bridge para esse contexto (porta, rede, env, e eventualmente DB/Redis compartilhados ou separados).

---

### 2. Serviço externo “registrado” no SinapUm

- O PayPi-Bridge continua **standalone** (por exemplo no `Source/PiNetwork/projects/PayPi-Bridge`, porta 9080).
- No **Core_SinapUm** (configuração ou banco) você **registra** o PayPi-Bridge como serviço:
  - URL base: `http://69.169.102.84:9080` (ou domínio futuro).
  - Nome: `paypibridge` (ou `PayPi-Bridge`).
  - Opcional: API key / header para chamadas server-to-server.
- O Core (e outros sistemas) passam a usar esse registro para:
  - Chamar `/api/checkout/pi-intent`, `/api/payments/verify`, `/api/pi/status`, `/api/consents`, `/api/payouts/pix`, etc.
  - Ou o Core expor um “proxy”/facade que repassa as requisições ao PayPi-Bridge (mesmo padrão de quando chama OpenMind ou MCP).

**Vantagens:** zero mudança no deploy atual do PayPi-Bridge; só configuração no SinapUm.

**Desvantagem:** mais um ponto de deploy e de rede (mas ainda “um serviço do SinapUm” do ponto de vista funcional).

---

## Recomendações práticas

1. **Curto prazo:** usar a **opção 2** (PayPi-Bridge standalone, registrado no SinapUm como serviço com URL e opcional API key). Assim ele já “é um serviço do SinapUm” sem mexer no compose do Core.
2. **Se quiser tudo no mesmo compose:** seguir a **opção 1**: adicionar o PayPi-Bridge como serviço no `docker-compose.yml` do Core_SinapUm, porta fixa (ex. 7030), e documentar no mesmo lugar que OpenMind, MCP e iFood.
3. **Documentação no SinapUm:** no documento de arquitetura (ex.: `ANALISE_ARQUITETURA_SISTEMAS_SINAPUM.md`) incluir uma linha na tabela de serviços, por exemplo:
   - **PayPi-Bridge** | `7030` (ou `9080`) | HTTP | Gateway Pi → BRL, checkout, verify, webhook CCIP, Open Finance.

---

## Resumo

- **Sim**, o PayPi-Bridge pode ser tratado como um serviço do SinapUm, como os outros.
- Pode ser **dentro do mesmo stack** (compose do Core) ou **fora**, apenas **registrado** (URL + nome + opcional API key).
- O que define “ser um serviço no SinapUm” é: ter URL estável, ser chamado pelo Core ou por outros sistemas Source, e estar documentado na arquitetura do SinapUm. O PayPi-Bridge já tem API REST pronta para isso.
