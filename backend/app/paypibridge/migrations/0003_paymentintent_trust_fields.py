from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("paypibridge", "0002_webhookevent"),
    ]

    operations = [
        migrations.AddField(
            model_name="paymentintent",
            name="confidence_level",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="paymentintent",
            name="ledger_checked",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="paymentintent",
            name="verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
