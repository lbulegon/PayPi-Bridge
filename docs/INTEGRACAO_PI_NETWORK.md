# Integração Pi Network – PayPi-Bridge

Como configurar e testar a integração com a Pi Network no PayPi-Bridge.

---

## 1. O que foi feito no código

- **SDK pi-python** está em `backend/pi_sdk/` (cópia para funcionar no Docker).
- O **PiService** usa apenas `backend/pi_sdk/` (PayPi-Bridge é autossuficiente).
- Endpoints que usam Pi:
  - **GET /api/pi/status** – status da integração (configurado ou não, sem expor credenciais)
  - **GET /api/pi/balance** – saldo da carteira do app
  - **POST /api/payments/verify** – verificar pagamento Pi e vincular ao PaymentIntent

---

## 2. Obter credenciais Pi Network

1. Acesse o **Pi Developer Portal**: https://develop.pi (ou o portal oficial atual).
2. Crie uma aplicação (ou use uma existente).
3. Anote:
   - **API Key** – chave da aplicação
   - **Wallet / Private key** – seed da carteira do app (começa com `S`, 56 caracteres)

Para testes use **Pi Testnet**; para produção use **Pi Network** (mainnet).

---

## 3. Configurar variáveis de ambiente

No servidor, edite o `.env` do PayPi-Bridge (ou use o mesmo no Docker):

```bash
# Pi Network
PI_API_KEY=sua_api_key_aqui
PI_WALLET_PRIVATE_SEED=S...sua_seed_56_caracteres
PI_NETWORK=Pi Testnet
```

- **PI_API_KEY**: API Key do Developer Portal  
- **PI_WALLET_PRIVATE_SEED**: seed da carteira (56 caracteres, começa com S)  
- **PI_NETWORK**: `Pi Testnet` (sandbox) ou `Pi Network` (mainnet)

---

## 4. Reiniciar o backend

Para carregar as novas variáveis:

```bash
cd /root/Source/PiNetwork/projects/PayPi-Bridge
docker compose restart backend
```

Aguarde ~15 segundos.

---

## 5. Testar a integração

1. Abra **http://69.169.102.84:9080/forms/**.
2. **Consultar saldo** – clique em “Consultar saldo”.  
   - Se estiver configurado: deve retornar algo como `{"balance": "0", "network": "Pi Testnet"}`.  
   - Se não: `{"detail": "Pi Network integration not available"}`.
3. **Verificar pagamento** – use **POST /api/payments/verify** com um `payment_id` e `intent_id` válidos (após um pagamento real ou fluxo de teste).

---

## 6. Resumo de endpoints Pi

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/pi/status` | GET | Status da integração Pi (configured, network, message) |
| `/api/pi/balance` | GET | Saldo da carteira do app |
| `/api/checkout/pi-intent` | POST | Criar PaymentIntent (não depende de Pi) |
| `/api/payments/verify` | POST | Verificar pagamento Pi e vincular ao intent |

---

## 7. Troubleshooting

- **"Pi Network integration not available"**  
  - Confirme `PI_API_KEY` e `PI_WALLET_PRIVATE_SEED` no `.env`.  
  - Confirme que o backend foi reiniciado após alterar o `.env`.

- **Saldo 0 ou erro ao consultar**  
  - Testnet: use conta e carteira de teste.  
  - Mainnet: use API Key e seed da app em produção.

- **Erro ao verificar pagamento**  
  - Confirme que o `payment_id` existe na Pi e que o `intent_id` existe no PayPi-Bridge.
