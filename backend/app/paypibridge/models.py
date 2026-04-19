from django.db import models
from django.utils import timezone
from django.conf import settings


class Tenant(models.Model):
    """Cliente da API (multi-tenant): cada integração tem chave e webhook."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=64, unique=True, db_index=True)
    api_key = models.CharField(max_length=128, unique=True, db_index=True)
    webhook_url = models.URLField(blank=True, default="")
    is_platform = models.BooleanField(
        default=False,
        help_text="Tenant interno da plataforma (recebe taxas em BRL).",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} ({self.slug})"


class Wallet(models.Model):
    """Saldo por ativo; atualizado apenas via LedgerEntry (serviço)."""

    ASSET_PI = "PI"
    ASSET_BRL = "BRL"
    ASSET_CHOICES = [(ASSET_PI, "PI"), (ASSET_BRL, "BRL")]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="wallets")
    asset = models.CharField(max_length=10, choices=ASSET_CHOICES)
    balance = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant", "asset"], name="paypibridge_wallet_tenant_asset_uniq"),
        ]

    def __str__(self):
        return f"{self.tenant.slug}:{self.asset}={self.balance}"


class LedgerEntry(models.Model):
    """Lançamento contábil imutável (crédito/débito por tenant e ativo)."""

    ENTRY_CREDIT = "credit"
    ENTRY_DEBIT = "debit"
    ENTRY_CHOICES = [(ENTRY_CREDIT, "credit"), (ENTRY_DEBIT, "debit")]

    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="ledger_entries")
    entry_type = models.CharField(max_length=10, choices=ENTRY_CHOICES)
    asset = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=28, decimal_places=8)
    reference = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    idempotency_key = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    payment_intent = models.ForeignKey(
        "PaymentIntent",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ledger_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["idempotency_key"],
                condition=models.Q(idempotency_key__isnull=False),
                name="paypibridge_ledgerentry_idempotency_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.entry_type} {self.amount} {self.asset} @{self.reference}"


class FeeConfig(models.Model):
    """Taxa percentual sobre o bruto em BRL (ex.: 0.025 = 2,5%)."""

    label = models.CharField(max_length=64, default="default")
    percentage = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        help_text="Taxa como decimal (0.025 = 2,5% sobre BRL bruto).",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]


class Settlement(models.Model):
    """Registo de liquidação Pix associado ao intent (auditoria)."""

    ST_PENDING = "pending"
    ST_PROCESSING = "processing"
    ST_COMPLETED = "completed"
    ST_FAILED = "failed"
    STATUS_CHOICES = [
        (ST_PENDING, "Pending"),
        (ST_PROCESSING, "Processing"),
        (ST_COMPLETED, "Completed"),
        (ST_FAILED, "Failed"),
    ]

    payment_intent = models.OneToOneField(
        "PaymentIntent",
        on_delete=models.CASCADE,
        related_name="settlement_record",
    )
    amount_brl = models.DecimalField(max_digits=20, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ST_PENDING)
    pix_txid = models.CharField(max_length=255, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settlement {self.payment_intent_id} {self.status}"


class Consent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.CharField(max_length=120)
    scope = models.JSONField(default=dict)
    consent_id = models.CharField(max_length=120, unique=True)
    status = models.CharField(max_length=32, default="ACTIVE")
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)

class BankAccount(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    consent = models.ForeignKey(Consent, on_delete=models.PROTECT)
    institution = models.CharField(max_length=120)
    account_id = models.CharField(max_length=120)
    branch = models.CharField(max_length=16, blank=True)
    number = models.CharField(max_length=32, blank=True)
    ispb = models.CharField(max_length=8, blank=True)

class PaymentIntent(models.Model):
    STATUS = [
        ("CREATED","CREATED"),("CONFIRMED","CONFIRMED"),
        ("SETTLED","SETTLED"),("CANCELLED","CANCELLED")
    ]
    PAY_ONE_TIME = "one_time"
    PAY_SUBSCRIPTION = "subscription"
    PAYMENT_TYPE_CHOICES = [
        (PAY_ONE_TIME, "one_time"),
        (PAY_SUBSCRIPTION, "subscription"),
    ]

    tenant = models.ForeignKey(
        Tenant,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="payment_intents",
    )
    source = models.CharField(max_length=20, default="PI")
    external_pi_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default=PAY_ONE_TIME,
    )

    intent_id = models.CharField(max_length=120, unique=True)
    payer_address = models.CharField(max_length=128)
    payee_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pi_payee")
    amount_pi = models.DecimalField(max_digits=20, decimal_places=8)
    amount_brl = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    fx_quote = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=STATUS, default="CREATED")
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    # Trust engine (Pi Platform + opcional Horizon)
    confidence_level = models.CharField(max_length=64, null=True, blank=True)
    ledger_checked = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    # Liquidação Pi → BRL → Pix (SettlementService)
    settlement_status = models.CharField(max_length=32, null=True, blank=True)
    settled_amount_brl = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    settlement_fee_brl = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    settlement_pix_txid = models.CharField(max_length=120, null=True, blank=True)

    def __str__(self):
        return self.intent_id

class Escrow(models.Model):
    intent = models.OneToOneField(PaymentIntent, on_delete=models.CASCADE, related_name="escrow")
    release_condition = models.CharField(max_length=64, default="DELIVERY_CONFIRMED")
    deadline = models.DateTimeField(null=True, blank=True)

class PixTransaction(models.Model):
    intent = models.ForeignKey(PaymentIntent, on_delete=models.PROTECT, related_name="pix")
    tx_id = models.CharField(max_length=120, unique=True)
    status = models.CharField(max_length=32)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)


class WebhookEvent(models.Model):
    """Eventos de webhook CCIP já processados (idempotência)."""
    intent_id = models.CharField(max_length=120, db_index=True)
    event_id = models.CharField(max_length=120)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["intent_id", "event_id"], name="paypibridge_webhook_intent_event_unique"),
        ]


# --- Versão 3: partidas dobradas, retry, idempotência API ---


class LedgerAccount(models.Model):
    """Plano de contas (double-entry): ativo, passivo ou receita."""

    CAT_ASSET = "ASSET"
    CAT_LIABILITY = "LIABILITY"
    CAT_REVENUE = "REVENUE"
    CATEGORY_CHOICES = [
        (CAT_ASSET, "ASSET"),
        (CAT_LIABILITY, "LIABILITY"),
        (CAT_REVENUE, "REVENUE"),
    ]

    TYPE_WALLET = "wallet"
    TYPE_FEE = "fee"
    TYPE_CLEARING = "clearing"
    TYPE_REVENUE = "revenue"
    TYPE_CHOICES = [
        (TYPE_WALLET, "wallet"),
        (TYPE_FEE, "fee"),
        (TYPE_CLEARING, "clearing"),
        (TYPE_REVENUE, "revenue"),
    ]

    tenant = models.ForeignKey(
        Tenant,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="ledger_accounts",
    )
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    asset = models.CharField(max_length=10)
    account_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    balance = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    wallet = models.OneToOneField(
        Wallet,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ledger_account",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.balance})"


class JournalBatch(models.Model):
    """Lançamento contábil balanceado (soma débitos = soma créditos)."""

    reference = models.CharField(max_length=255)
    idempotency_key = models.CharField(max_length=128, null=True, blank=True, unique=True)
    payment_intent = models.ForeignKey(
        PaymentIntent,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="journal_batches",
    )
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]


class JournalLine(models.Model):
    """Linha de diário: montante sempre positivo; lado debit ou credit."""

    SIDE_DEBIT = "debit"
    SIDE_CREDIT = "credit"
    SIDE_CHOICES = [(SIDE_DEBIT, "debit"), (SIDE_CREDIT, "credit")]

    journal = models.ForeignKey(
        JournalBatch,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    account = models.ForeignKey(
        LedgerAccount,
        on_delete=models.PROTECT,
        related_name="journal_lines",
    )
    side = models.CharField(max_length=10, choices=SIDE_CHOICES)
    amount = models.DecimalField(max_digits=28, decimal_places=8)

    class Meta:
        ordering = ["id"]


class RetryTask(models.Model):
    """Tarefas com retry exponencial (resiliência)."""

    ST_PENDING = "pending"
    ST_DONE = "done"
    ST_FAILED = "failed"
    STATUS_CHOICES = [
        (ST_PENDING, "pending"),
        (ST_DONE, "done"),
        (ST_FAILED, "failed"),
    ]

    task_type = models.CharField(max_length=50, db_index=True)
    payload = models.JSONField(default=dict)
    retries = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ST_PENDING)
    next_attempt = models.DateTimeField(db_index=True)
    last_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["next_attempt", "id"]


class IdempotencyRecord(models.Model):
    """Respostas idempotentes para APIs (ex.: POST /api/v3/payments)."""

    scope = models.CharField(max_length=64)
    key = models.CharField(max_length=255)
    response_body = models.JSONField(default=dict)
    status_code = models.PositiveSmallIntegerField(default=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["scope", "key"], name="paypibridge_idempotency_scope_key_uniq"),
        ]
