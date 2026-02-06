# Pi Network SDK – PayPi-Bridge

Este diretório contém o **SDK pi-python** usado pelo PayPi-Bridge para integração com a Pi Network.

- **Origem:** https://github.com/pi-apps/pi-python  
- **Uso:** saldo da carteira (`get_balance`), verificação de pagamento (`get_payment`), criação/envio de pagamentos (A2U).

## Conteúdo

- `pi_python.py` – classe `PiNetwork` (API Pi + Stellar SDK)
- `__init__.py` – marca o pacote

## Dependências

Já presentes em `backend/requirements.txt`:

- `requests`
- `stellar-sdk`

## Configuração

Variáveis de ambiente (no `.env` do PayPi-Bridge):

- `PI_API_KEY` – API Key do app no Developer Portal
- `PI_WALLET_PRIVATE_SEED` – seed da carteira (56 caracteres, começa com `S`)
- `PI_NETWORK` – `Pi Testnet` ou `Pi Network`

Ver `docs/INTEGRACAO_PI_NETWORK.md` para o passo a passo completo.
