# Generated manually for PayPi-Bridge

from django.conf import settings
from django.db import migrations, models
from django.utils import timezone
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Consent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(max_length=120)),
                ("scope", models.JSONField(default=dict)),
                ("consent_id", models.CharField(max_length=120, unique=True)),
                ("status", models.CharField(default="ACTIVE", max_length=32)),
                ("created_at", models.DateTimeField(default=timezone.now)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="PaymentIntent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("intent_id", models.CharField(max_length=120, unique=True)),
                ("payer_address", models.CharField(max_length=128)),
                ("amount_pi", models.DecimalField(decimal_places=8, max_digits=20)),
                ("amount_brl", models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ("fx_quote", models.JSONField(default=dict)),
                ("status", models.CharField(choices=[("CREATED", "CREATED"), ("CONFIRMED", "CONFIRMED"), ("SETTLED", "SETTLED"), ("CANCELLED", "CANCELLED")], default="CREATED", max_length=16)),
                ("metadata", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(default=timezone.now)),
                ("payee_user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pi_payee", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="BankAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("institution", models.CharField(max_length=120)),
                ("account_id", models.CharField(max_length=120)),
                ("branch", models.CharField(blank=True, max_length=16)),
                ("number", models.CharField(blank=True, max_length=32)),
                ("ispb", models.CharField(blank=True, max_length=8)),
                ("consent", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="paypibridge.consent")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Escrow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("release_condition", models.CharField(default="DELIVERY_CONFIRMED", max_length=64)),
                ("deadline", models.DateTimeField(blank=True, null=True)),
                ("intent", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="escrow", to="paypibridge.paymentintent")),
            ],
        ),
        migrations.CreateModel(
            name="PixTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tx_id", models.CharField(max_length=120, unique=True)),
                ("status", models.CharField(max_length=32)),
                ("payload", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(default=timezone.now)),
                ("intent", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pix", to="paypibridge.paymentintent")),
            ],
        ),
    ]
