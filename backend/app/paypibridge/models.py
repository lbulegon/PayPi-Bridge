from django.db import models
from django.utils import timezone
from django.conf import settings

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
    intent_id = models.CharField(max_length=120, unique=True)
    payer_address = models.CharField(max_length=128)
    payee_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pi_payee")
    amount_pi = models.DecimalField(max_digits=20, decimal_places=8)
    amount_brl = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    fx_quote = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=STATUS, default="CREATED")
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)

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
