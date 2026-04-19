# V3: double-entry accounts, journal, retry queue, idempotency records

from decimal import Decimal

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def seed_ledger_accounts(apps, schema_editor):
    Wallet = apps.get_model("paypibridge", "Wallet")
    LedgerAccount = apps.get_model("paypibridge", "LedgerAccount")

    if LedgerAccount.objects.filter(code="CLEARING_PI").exists():
        return

    LedgerAccount.objects.create(
        code="CLEARING_PI",
        name="Clearing Pi (ativo)",
        asset="PI",
        account_type="clearing",
        category="ASSET",
        balance=Decimal("0"),
    )
    LedgerAccount.objects.create(
        code="CLEARING_BRL",
        name="Clearing BRL (ativo)",
        asset="BRL",
        account_type="clearing",
        category="ASSET",
        balance=Decimal("0"),
    )
    LedgerAccount.objects.create(
        code="PLATFORM_FEE_BRL",
        name="Receita de taxas BRL",
        asset="BRL",
        account_type="revenue",
        category="REVENUE",
        balance=Decimal("0"),
    )

    for w in Wallet.objects.all().select_related("tenant"):
        code = f"WALLET_T{w.tenant_id}_{w.asset}"
        bal = w.balance or Decimal("0")
        LedgerAccount.objects.update_or_create(
            code=code,
            defaults={
                "tenant_id": w.tenant_id,
                "name": f"Wallet {w.tenant.slug} {w.asset}",
                "asset": w.asset,
                "account_type": "wallet",
                "category": "LIABILITY",
                "balance": bal,
                "wallet": w,
            },
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("paypibridge", "0005_tenant_wallet_ledger_v2"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="LedgerAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(db_index=True, max_length=64, unique=True)),
                ("name", models.CharField(max_length=100)),
                ("asset", models.CharField(max_length=10)),
                (
                    "account_type",
                    models.CharField(
                        choices=[
                            ("wallet", "wallet"),
                            ("fee", "fee"),
                            ("clearing", "clearing"),
                            ("revenue", "revenue"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[("ASSET", "ASSET"), ("LIABILITY", "LIABILITY"), ("REVENUE", "REVENUE")],
                        max_length=20,
                    ),
                ),
                ("balance", models.DecimalField(decimal_places=8, default=0, max_digits=28)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ledger_accounts",
                        to="paypibridge.tenant",
                    ),
                ),
                (
                    "wallet",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ledger_account",
                        to="paypibridge.wallet",
                    ),
                ),
            ],
            options={"ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="JournalBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference", models.CharField(max_length=255)),
                ("idempotency_key", models.CharField(blank=True, max_length=128, null=True, unique=True)),
                ("metadata", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "payment_intent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="journal_batches",
                        to="paypibridge.paymentintent",
                    ),
                ),
            ],
            options={"ordering": ["-id"]},
        ),
        migrations.CreateModel(
            name="JournalLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("side", models.CharField(choices=[("debit", "debit"), ("credit", "credit")], max_length=10)),
                ("amount", models.DecimalField(decimal_places=8, max_digits=28)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="journal_lines",
                        to="paypibridge.ledgeraccount",
                    ),
                ),
                (
                    "journal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lines",
                        to="paypibridge.journalbatch",
                    ),
                ),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="RetryTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("task_type", models.CharField(db_index=True, max_length=50)),
                ("payload", models.JSONField(default=dict)),
                ("retries", models.PositiveIntegerField(default=0)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "pending"),
                            ("done", "done"),
                            ("failed", "failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("next_attempt", models.DateTimeField(db_index=True)),
                ("last_error", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["next_attempt", "id"]},
        ),
        migrations.CreateModel(
            name="IdempotencyRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scope", models.CharField(max_length=64)),
                ("key", models.CharField(max_length=255)),
                ("response_body", models.JSONField(default=dict)),
                ("status_code", models.PositiveSmallIntegerField(default=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name="idempotencyrecord",
            constraint=models.UniqueConstraint(fields=("scope", "key"), name="paypibridge_idempotency_scope_key_uniq"),
        ),
        migrations.RunPython(seed_ledger_accounts, noop),
    ]
