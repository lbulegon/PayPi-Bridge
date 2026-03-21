# Curso Técnico de Pi Network e Rede Stellar (didático e profundamente técnico)

Este material foi preparado para estudo, pesquisa e aulas. Ele foca **infraestrutura, arquitetura de nós, protocolo de consenso (SCP), observabilidade, segurança e economia do ecossistema**.

**Avisos importantes (para segurança educacional):**
- Não é recomendação de investimento.
- “Economia do Pi” e mecanismos de incentivo podem mudar ao longo do tempo; use fontes oficiais do Pi Network.
- Não compartilhe segredos do node (ex.: `NODE_PRIVATE_KEY` / seeds).

---

## Visão geral do curso

### Objetivos de aprendizagem
Ao final, o aluno deve ser capaz de:
- Explicar o que é a rede Pi (mainnet/testnet) e como ela usa base tecnológica do Stellar.
- Explicar, em nível técnico, o **Stellar Consensus Protocol (SCP)**: quorum slices, quorum sets, phases (prepare/confirm, externalize/internalize), e implicações de segurança.
- Mapear a arquitetura do node: **stellar-core, Horizon, PostgreSQL, history/captive**, e o papel dos validadores.
- Compreender como o `pi-node` configura e opera o `stellar-core` e como “estado sincronizado” se traduz em saúde operacional.
- Definir um conjunto de boas práticas de **segurança operacional** para maximizar confiabilidade (UFW/firewall, atualizações, monitorização, limites de recurso, backups).
- Entender o lado econômico do Pi em termos conceituais: mineração/participação (na camada do ecossistema), “lockup commitment” (conceito similar a staking do ponto de vista de comprometimento de longo prazo), e como pensar em risco/portunidade.
- Discutir possibilidades de onramps/corretores e como isso se relaciona com liquidez e mercado (sem prometer retornos).

### Pré-requisitos
- Linux básico (systemd, logs, permissões)
- Docker básico (compose, volumes)
- Fundamentos de redes (TCP/UDP, NAT, portas)
- Conceitos básicos de blockchain/ledger

---

## Estrutura do curso (módulos)

### Módulo 0 — Fundamentos e laboratório
- O que o curso vai cobrir e como estudar
- Prática: preparar ambiente, entender portas do Pi Node e coletar logs

### Módulo 1 — Stellar: ledger, contas e modelo de dados
- Accounts, balances, trustlines, offers
- Transações, operações e efeito no ledger
- Horizon e acesso programático (REST)
- Bucket storage e history/catchup

### Módulo 2 — Stellar Consensus Protocol (SCP) em profundidade
- Problema: acordo distribuído sem proof-of-work
- Federated Byzantine Agreement (FBA)
- Quorum sets e quorum slices
- Ballots, nominations e confirmations (visão conceitual)
- Segurança e propriedades (safety/liveness) por configuração
- Externalize/internalize e impacto no “fecho” de ledger
- Por que “quorum 2/3” (no teu config) influencia disponibilidade

### Módulo 3 — Pi Network: arquitetura e mapeamento técnico no teu node
- Passphrase de rede e isolamento de consenso
- Validadores oficiais (os 3 do mainnet)
- O teu node como watcher/non-validator
- Componentes: stellar-core, Horizon, PostgreSQL, supervisord e volumes
- Persistência de configuração no volume: por que `.env` nem sempre muda a config efetiva

### Módulo 4 — Nós, conectividade e portas
- P2P: PEER_PORT e tráfego
- API/Horizon: endpoints e ingest
- History/captive core: por que existe e como funciona
- IN/OUT peers e o que significa para P2P

### Módulo 5 — Observabilidade e saúde operacional
- Estados: `Starting up`, `Catching`, `Synced`
- Lag de ingest e lag de quorum
- Métricas e sinais: CPU/Mem/disk I/O
- Logs: padrões esperados vs problemas

### Módulo 6 — Segurança operacional (hardening)
- Firewall, UFW e segmentação
- Minimização de superfície (não expor admin)
- Gestão de segredos e permissões de ficheiros
- Atualizações: protocolo e compatibilidade de ledger
- Threat model do ponto de vista do node

### Módulo 7 — Economia do Pi Network (educacional)
- Modelo de incentivos e mecanismos (miner/participação)
- Lockup commitment como “compromisso de longo prazo”
- Rewards e como pensar em segurança econômica (sem garantia)
- Relação entre participação do ecossistema e infraestrutura (node reliability)

### Módulo 8 — Mercado, liquidez e onramp (educacional)
- Onramps e mecânica geral (custódia, compliance, KYB)
- Como avaliar caminho de liquidez e riscos
- Como diferenciar marketing vs mecânica técnica

### Módulo 9 — Investment/stake/risco: estrutura de análise
- Como construir um checklist de risco
- O que significa “stake” vs “lockup commitment” no contexto conceitual
- Custos de oportunidade
- Riscos regulatórios e de liquidez

### Módulo 10 — Capstone e avaliações
- Capstone: “auditar e elevar saúde do node”
- Trabalho: documentar, propor e aplicar melhorias com rollback seguro

---

## Módulo 2 — SCP (Stellar Consensus Protocol) detalhado (núcleo técnico)

> Esta seção é o “coração” do curso técnico. Ela deve ser apresentada com exemplos visuais e exercícios.

### 2.1 Por que SCP existe
Redes baseadas em proof-of-work/proof-of-stake exigem suposições específicas (energia, stake, slashing, etc.). O SCP foi projetado para:
- Permitir consenso com baixa latência
- Evitar depender apenas de potência computacional
- Usar relações de confiança definidas pelos operadores (federated approach)

### 2.2 Modelo FBA (Federated Byzantine Agreement)
No FBA, cada nó define:
- Quais nós ele “confia”
- Como esses nós se combinam em grupos (quorum slices)

Assim, em vez de existir um único conjunto global de validadores, existem múltiplos conjuntos sobrepostos de confiança.

### 2.3 Quorum sets, quorum slices e thresholds
- Um **quorum set** descreve um conjunto de nós que, quando suficientes, permitem decisões do consenso.
- Uma **quorum slice** é um subconjunto interno do quorum set.
- O **threshold** define quantos “membros suficientes” precisam concordar.

No teu `stellar-core.cfg` aparece uma estrutura que corresponde a um quorum do tipo “quorum com fail_at=2” e “transitive node_count”. Isso, conceitualmente, comunica que:
- há tolerância a falhas até um certo número
- passar disso impede finalização/continuidade do protocolo

### 2.4 Ballots, nominations e confirmations (visão conceitual)
SCP usa mensagens de consenso que podem ser vistas como fases de:
- Propor um valor/estado candidato para o próximo ledger (ou próximo passo de consenso)
- Confirmar/validar o que outros nós aceitam dentro dos seus quorum slices
- Externalizar quando há consenso suficiente

A externalização é relevante porque ela marca decisões que o resto da rede passa a tratar como estáveis.

### 2.5 Externalize vs Catchup vs Synced
No teu ambiente, observamos:
- `Catching up` / `Catching`
- `EXTERNALIZE` na fase do quorum
- `Synced!` no pi-node status

Interpretação didática:
- “Catching up” significa que o node ainda está atrás de ledgers recentes e precisa completar a sincronização.
- “Externalize” indica que o consenso já chegou a um ponto em que ledgers recentes estão sendo finalizados logicamente de forma consistente.
- “Synced!” indica que a camada de dados do node (core e horizon/ingest) atingiu o ponto de estar em dia.

### 2.6 Segurança e disponibilidade (trade-off central)
A segurança do SCP vem de:
- interseções entre quorum sets
- propriedades de overlap (e “intersection checker”)

A disponibilidade vem da configuração do quorum:
- “se 1 validador falha, rede continua”
- “se 2 falham, rede para”

Em termos operacionais, isso se traduz em:
- redundância e atualização segura dos nós críticos
- monitorização e resiliência

---

## Módulo 3 — Pi Network no teu node (arquitetura prática)

### 3.1 Isolamento de rede por passphrase
`NETWORK_PASSPHRASE = "Pi Network"` significa que o node participa do consenso **somente** no universo Pi.

### 3.2 3 validadores oficiais e o teu papel
No teu `stellar-core.cfg`, os 3 validadores são listados em `[[VALIDATORS]]` com:
- `PUBLIC_KEY`
- `ADDRESS`
- `HISTORY` (URL do archive)

Seu node tipicamente não é validador:
- `NODE_IS_VALIDATOR = false`

Logo, seu papel é:
- manter cópia do ledger
- sincronizar com os validadores
- servir dados/atuar como parte do ecossistema

### 3.3 Persistência e “por que alterar `.env` às vezes não muda a seed efetiva”
Em stacks docker, a config pode existir:
- no `.env` (variáveis para o compose)
- em ficheiros gerados no volume (ex.: `stellar-core.cfg` dentro do volume)

Se o entrypoint do container detecta que o diretório/arquivo já existe, ele pode “skip” de inicialização. Assim, a alteração de `.env` pode não refletir automaticamente.

---

## Módulo 5 — Observabilidade: como transformar sinais técnicos em decisão

### 5.1 O que medir e por quê
- `Protocol State` (Catching/Synced)
- `Horizon ingest lag` (quanto está atrasado)
- `Lag do quorum` (quanto tempo está para consensuar)
- versão do `stellar-core` (compatibilidade com ledger)

### 5.2 Logs como “telemetria” de saúde
No teu histórico apareceram padrões importantes:
- `unsupported ledger version` durante catchup
- falhas repetidas por endpoint de info (Horizon → core)

No curso, ensine o aluno a distinguir:
- erros transitórios esperados
- erros de compatibilidade (update necessário)
- erros de configuração (endpoint/URL/portas)

---

## Módulo 6 — Segurança operacional (threat model do node)

### 6.1 Segurança de rede
- permitir somente portas necessárias
- garantir roteabilidade das portas do P2P

### 6.2 Segurança de processos e segredos
- seeds privadas devem ser tratadas como chaves de carteira
- permissões corretas em ficheiros de config
- logs não devem vazar segredos

### 6.3 Segurança de disponibilidade
- atualizar de forma coordenada (evita incompatibilidade de ledger)
- manter backup do compose e configs

---

## Módulo 7 — Economia do Pi Network (educacional, sem promessas)

### 7.1 O que “Pi representa” em termos de ecossistema
O Pi Network é um ecossistema que combina:
- participação por atividade (mining no celular)
- incentivos de comunidade
- infra de nós (como o teu node)

### 7.2 “Staking” vs lockup commitment (conceito)
Fontes oficiais tendem a descrever que não existe necessariamente staking no formato tradicional (como em PoS clássico). O mecanismo mais próximo do conceito econômico de “compromisso de longo prazo” é o **lockup commitment**, que funciona como:
- compromisso configurável
- potencialmente impacta “merit”/rewards no ecossistema

Para o curso, trate assim:
- “staking” como conceito de comprometimento e risco de longo prazo
- “lockup commitment” como mecanismo específico do Pi

### 7.3 Rewards e node
O Pi Node tende a ser recompensado com base em confiabilidade/participação, e essa confiabilidade é tecnicamente afetada por:
- uptime
- conectividade
- compatibilidade de versão
- ingest lag

---

## Módulo 8 — Onramps, liquidez e padrão de mercado (educacional)

### 8.1 Como pensar em onramp
Onramps normalmente conectam:
- usuário final
- provedor regulado/custódia
- infraestrutura de liquidez

Riscos gerais para o aluno:
- custódia e compliance
- spreads e volatilidade
- risco de contraparte

### 8.2 Padrões de mercado
Em exchanges e mercados de CEX/DEX/Custody, os pontos típicos:
- pares de negociação (ex.: PI/USDT)
- depósitos/saques (rede e custódia)
- regras KYB/KYC

---

## Módulo 9 — Investment/Stake: checklist de risco (educacional)

### 9.1 Checklist técnico-econômico
- risco de liquidez
- risco regulatório
- risco operacional (uptime e compatibilidade do node)
- risco de “mecanismo mudar” (protocol updates, incentivos)

### 9.2 Como evitar armadilhas
- Nunca tratar promessas de retorno como garantias
- Comparar com cenários de baixa liquidez e alta volatilidade

---

## Labs e exercícios (recomendado para aulas)

### Lab A — Mapear a configuração do teu node
Exercícios:
- ler `stellar-core.cfg`
- extrair `NODE_SEED`/`NODE_IS_VALIDATOR`
- listar `[[VALIDATORS]]` e interpretar quorum set

Comandos (exemplo didático):
- `cat /var/lib/pi-node/docker_volumes/mainnet/stellar/core/etc/stellar-core.cfg`

### Lab B — Medir estado e correlacionar com logs
Exercícios:
- rodar `pi-node status`
- observar transição Catching → Synced
- capturar logs de erros recorrentes e classificar causa

### Lab C — Segurança operacional
Exercícios:
- revisar UFW
- validar portas expostas no host e container
- desabilitar/ativar auto-update e comparar efeitos em saúde e logs

---

## Avaliação final (capstone)

Projeto: “Elevar confiabilidade do node”
- criar baseline (status + métricas + erros)
- identificar causa raiz (compatibilidade, portas, endpoints, versão)
- aplicar correção com rollback
- re-checar ingest lag e erros recentes

---

## Referências iniciais (pontos de partida)
- Documentação do Pi Network (Pi Node e FAQs)
- Documentação e blog técnico da Stellar (Stellar Consensus Protocol)
- Arquivos do teu próprio node (`stellar-core.cfg`, logs, horizon.env)

---

## Relação com o projeto PayPi-Bridge

Este curso foca **nó / ledger / SCP / Horizon**. O PayPi-Bridge integra a **Pi Platform** via SDK (`PiService`), camada distinta. Para alinhar objetivos de produto, operação e próximos passos, ver **[`MAPEAMENTO_CURSO_PI_PAYPI_BRIDGE.md`](MAPEAMENTO_CURSO_PI_PAYPI_BRIDGE.md)**.
