# Generated migration for PPBridge Service

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django.core.validators
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BridgeFlow',
            fields=[
                ('flow_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('source_domain', models.CharField(max_length=32)),
                ('source_adapter', models.CharField(max_length=64)),
                ('source_metadata', models.JSONField(blank=True, default=dict)),
                ('target_domain', models.CharField(max_length=32)),
                ('target_adapter', models.CharField(max_length=64)),
                ('target_metadata', models.JSONField(blank=True, default=dict)),
                ('asset', models.CharField(max_length=16)),
                ('amount', models.DecimalField(decimal_places=8, max_digits=20, validators=[django.core.validators.MinValueValidator(0)])),
                ('status', models.CharField(choices=[('INITIATED', 'INITIATED'), ('VALIDATED', 'VALIDATED'), ('BRIDGING', 'BRIDGING'), ('CONVERTED', 'CONVERTED'), ('COMPLETED', 'COMPLETED'), ('FAILED', 'FAILED'), ('CANCELED', 'CANCELED')], default='INITIATED', max_length=16)),
                ('result', models.JSONField(blank=True, default=dict)),
                ('error_code', models.CharField(blank=True, max_length=64)),
                ('error_message', models.TextField(blank=True)),
                ('callback_url', models.URLField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('idempotency_key', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'bridge_flows',
            },
        ),
        migrations.CreateModel(
            name='FlowEvent',
            fields=[
                ('event_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_type', models.CharField(choices=[('FLOW_CREATED', 'FLOW_CREATED'), ('STATE_CHANGE', 'STATE_CHANGE'), ('WEBHOOK_SENT', 'WEBHOOK_SENT'), ('WEBHOOK_FAILED', 'WEBHOOK_FAILED'), ('ERROR', 'ERROR'), ('ADAPTER_VALIDATION', 'ADAPTER_VALIDATION'), ('ADAPTER_EXECUTION', 'ADAPTER_EXECUTION')], max_length=32)),
                ('from_state', models.CharField(blank=True, max_length=16)),
                ('to_state', models.CharField(blank=True, max_length=16)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('correlation_id', models.CharField(blank=True, db_index=True, max_length=255)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('flow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='bridge.bridgeflow')),
            ],
            options={
                'db_table': 'bridge_flow_events',
                'ordering': ['timestamp'],
            },
        ),
        migrations.CreateModel(
            name='IdempotencyRecord',
            fields=[
                ('idempotency_key', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('request_hash', models.CharField(db_index=True, max_length=64)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('flow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='idempotency_records', to='bridge.bridgeflow')),
            ],
            options={
                'db_table': 'bridge_idempotency_records',
            },
        ),
        migrations.CreateModel(
            name='WebhookDelivery',
            fields=[
                ('delivery_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('url', models.URLField()),
                ('payload', models.JSONField()),
                ('signature', models.CharField(max_length=128)),
                ('status_code', models.IntegerField(blank=True, null=True)),
                ('response_body', models.TextField(blank=True)),
                ('attempt', models.IntegerField(default=1)),
                ('max_attempts', models.IntegerField(default=3)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('flow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='webhook_deliveries', to='bridge.bridgeflow')),
            ],
            options={
                'db_table': 'bridge_webhook_deliveries',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='bridgeflow',
            index=models.Index(fields=['status'], name='bridge_flow_status_idx'),
        ),
        migrations.AddIndex(
            model_name='bridgeflow',
            index=models.Index(fields=['idempotency_key'], name='bridge_flow_idempotency_key_idx'),
        ),
        migrations.AddIndex(
            model_name='bridgeflow',
            index=models.Index(fields=['created_at'], name='bridge_flow_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='flowevent',
            index=models.Index(fields=['flow', 'timestamp'], name='bridge_flow_flow_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='flowevent',
            index=models.Index(fields=['correlation_id'], name='bridge_flow_correlation_id_idx'),
        ),
        migrations.AddIndex(
            model_name='idempotencyrecord',
            index=models.Index(fields=['request_hash'], name='bridge_idempotency_request_hash_idx'),
        ),
        migrations.AddIndex(
            model_name='webhookdelivery',
            index=models.Index(fields=['flow', 'created_at'], name='bridge_webhook_flow_created_at_idx'),
        ),
    ]
