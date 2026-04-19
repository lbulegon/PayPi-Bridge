# Generated manually — multi-tenant, wallet, ledger, fee, settlement

from decimal import Decimal

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def seed_platform_and_fee(apps, schema_editor):
    Tenant = apps.get_model("paypibridge", "Tenant")
    Wallet = apps.get_model("paypibridge", "Wallet")
    FeeConfig = apps.get_model("paypibridge", "FeeConfig")
    if Tenant.objects.filter(slug="platform").exists():
        return
    t = Tenant.objects.create(
        name="Platform",
        slug="platform",
        api_key="ppb_platform_dev_key",
        webhook_url="",
        is_platform=True,
    )
    Wallet.objects.create(tenant=t, asset="PI", balance=Decimal("0"))
    Wallet.objects.create(tenant=t, asset="BRL", balance=Decimal("0"))
    FeeConfig.objects.create(label="default", percentage=Decimal("0"), is_active=True)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("paypibridge", "0004_paymentintent_settlement_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Tenant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=64, unique=True)),
                ("api_key", models.CharField(db_index=True, max_length=128, unique=True)),
                ("webhook_url", models.URLField(blank=True, default="")),
                (
                    "is_platform",
                    models.BooleanField(
                        default=False,
                        help_text="Tenant interno da plataforma (recebe taxas em BRL).",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="FeeConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("label", models.CharField(default="default", max_length=64)),
                (
                    "percentage",
                    models.DecimalField(
                        decimal_places=6,
                        help_text="Taxa como decimal (0.025 = 2,5% sobre BRL bruto).",
                        max_digits=10,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-id"]},
        ),
        migrations.CreateModel(
            name="Wallet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("asset", models.CharField(choices=[("PI", "PI"), ("BRL", "BRL")], max_length=10)),
                ("balance", models.DecimalField(decimal_places=8, default=0, max_digits=28)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wallets",
                        to="paypibridge.tenant",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="wallet",
            constraint=models.UniqueConstraint(fields=("tenant", "asset"), name="paypibridge_wallet_tenant_asset_uniq"),
        ),
        migrations.CreateModel(
            name="LedgerEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("entry_type", models.CharField(choices=[("credit", "credit"), ("debit", "debit")], max_length=10)),
                ("asset", models.CharField(max_length=10)),
                ("amount", models.DecimalField(decimal_places=8, max_digits=28)),
                ("reference", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("idempotency_key", models.CharField(blank=True, db_index=True, max_length=128, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ledger_entries",
                        to="paypibridge.tenant",
                    ),
                ),
                (
                    "payment_intent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ledger_entries",
                        to="paypibridge.paymentintent",
                    ),
                ),
            ],
            options={"ordering": ["-id"]},
        ),
        migrations.AddConstraint(
            model_name="ledgerentry",
            constraint=models.UniqueConstraint(
                condition=models.Q(idempotency_key__isnull=False),
                fields=("idempotency_key",),
                name="paypibridge_ledgerentry_idempotency_uniq",
            ),
        ),
        migrations.CreateModel(
            name="Settlement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount_brl", models.DecimalField(decimal_places=2, max_digits=20)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("pix_txid", models.CharField(blank=True, default="", max_length=255)),
                ("error_message", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "payment_intent",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="settlement_record",
                        to="paypibridge.paymentintent",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="paymentintent",
            name="tenant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="payment_intents",
                to="paypibridge.tenant",
            ),
        ),
        migrations.AddField(
            model_name="paymentintent",
            name="source",
            field=models.CharField(default="PI", max_length=20),
        ),
        migrations.AddField(
            model_name="paymentintent",
            name="external_pi_id",
            field=models.CharField(blank=True, db_index=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="paymentintent",
            name="payment_type",
            field=models.CharField(
                choices=[("one_time", "one_time"), ("subscription", "subscription")],
                default="one_time",
                max_length=20,
            ),
        ),
        migrations.RunPython(seed_platform_and_fee, noop),
    ]
