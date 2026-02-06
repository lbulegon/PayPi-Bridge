# Generated for Sprint 4 - Webhook CCIP idempotency

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("paypibridge", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="WebhookEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("intent_id", models.CharField(db_index=True, max_length=120)),
                ("event_id", models.CharField(max_length=120)),
                ("created_at", models.DateTimeField(default=timezone.now)),
            ],
        ),
        migrations.AddConstraint(
            model_name="webhookevent",
            constraint=models.UniqueConstraint(
                fields=("intent_id", "event_id"),
                name="paypibridge_webhook_intent_event_unique",
            ),
        ),
    ]
