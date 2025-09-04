CREATE TABLE consent (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL,
  provider VARCHAR(120) NOT NULL,
  scope JSONB NOT NULL DEFAULT '{}'::jsonb,
  consent_id VARCHAR(120) UNIQUE NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMP NULL
);

CREATE TABLE bank_account (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL,
  consent_id INTEGER NOT NULL REFERENCES consent(id),
  institution VARCHAR(120) NOT NULL,
  account_id VARCHAR(120) NOT NULL,
  branch VARCHAR(16),
  number VARCHAR(32),
  ispb VARCHAR(8)
);

CREATE TABLE payment_intent (
  id SERIAL PRIMARY KEY,
  intent_id VARCHAR(120) UNIQUE NOT NULL,
  payer_address VARCHAR(128) NOT NULL,
  payee_user_id INTEGER NOT NULL,
  amount_pi NUMERIC(20,8) NOT NULL,
  amount_brl NUMERIC(20,2),
  fx_quote JSONB NOT NULL DEFAULT '{}'::jsonb,
  status VARCHAR(16) NOT NULL DEFAULT 'CREATED',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE escrow (
  id SERIAL PRIMARY KEY,
  intent_id INTEGER NOT NULL UNIQUE REFERENCES payment_intent(id) ON DELETE CASCADE,
  release_condition VARCHAR(64) NOT NULL DEFAULT 'DELIVERY_CONFIRMED',
  deadline TIMESTAMP NULL
);

CREATE TABLE pix_transaction (
  id SERIAL PRIMARY KEY,
  intent_id INTEGER NOT NULL REFERENCES payment_intent(id),
  tx_id VARCHAR(120) UNIQUE NOT NULL,
  status VARCHAR(32) NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE audit_log (
  id SERIAL PRIMARY KEY,
  topic VARCHAR(80) NOT NULL,
  ref VARCHAR(120),
  data JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
