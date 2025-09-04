#![no_std]

use soroban_sdk::{contract, contractimpl, symbol_short, Address, Env, Symbol, Vec, BytesN, Map};

#[contract]
pub struct PayPiBridge;

const INTENTS: Symbol = symbol_short!("INTS");

#[contractimpl]
impl PayPiBridge {
    pub fn create_intent(env: Env, payer: Address, payee: Address, amount_pi: i128, ttl_secs: u64) -> BytesN<32> {
        payer.require_auth();
        let now = env.ledger().timestamp();
        let expires = now + ttl_secs;
        let id = env.crypto().sha256(&env.random().into());
        let mut store: Map<BytesN<32>, Vec<i128>> = env.storage().instance().get(&INTENTS).unwrap_or(Map::new(&env));
        let mut v: Vec<i128> = Vec::new(&env);
        v.push_back(amount_pi);
        v.push_back(expires as i128);
        store.set(id.clone(), v);
        env.storage().instance().set(&INTENTS, &store);
        env.events().publish(
            (symbol_short!("IntentCreated"),),
            (id.clone(), payer, payee, amount_pi, expires),
        );
        id
    }

    pub fn confirm_delivery(env: Env, intent_id: BytesN<32>, confirmer: Address) {
        confirmer.require_auth();
        env.events().publish(
            (symbol_short!("DeliveryConfirmed"),),
            (intent_id, confirmer),
        );
    }

    pub fn cancel_intent(env: Env, intent_id: BytesN<32>, caller: Address) {
        caller.require_auth();
        env.events().publish(
            (symbol_short!("IntentCancelled"),),
            (intent_id, caller),
        );
    }
}
