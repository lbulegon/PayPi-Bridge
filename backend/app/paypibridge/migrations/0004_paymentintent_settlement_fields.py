from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("paypibridge", "0003_paymentintent_trust_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="paymentintent",
            name="settlement_status",
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name="paymentintent",
            name="settled_amount_brl",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=20, null=True
            ),
        ),
        migrations.AddField(
            model_name="paymentintent",
            name="settlement_fee_brl",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=20, null=True
            ),
        ),
        migrations.AddField(
            model_name="paymentintent",
            name="settlement_pix_txid",
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
    ]
