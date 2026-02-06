from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import PaymentIntent, PixTransaction, Consent, BankAccount


class CreateIntentSerializer(serializers.Serializer):
    payee_user_id = serializers.IntegerField()
    amount_pi = serializers.DecimalField(max_digits=20, decimal_places=8)
    metadata = serializers.DictField(required=False)

    def validate_payee_user_id(self, value):
        if not get_user_model().objects.filter(id=value).exists():
            raise serializers.ValidationError("Usuário com este id não existe. Crie um com createtestuser.")
        return value


class VerifyPaymentSerializer(serializers.Serializer):
    payment_id = serializers.CharField(max_length=120)
    intent_id = serializers.CharField(max_length=120)


class PaymentIntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentIntent
        fields = "__all__"


class PixPayoutSerializer(serializers.Serializer):
    payee_user_id = serializers.IntegerField()
    amount_brl = serializers.DecimalField(max_digits=20, decimal_places=2)
    cpf = serializers.CharField(max_length=11)
    pix_key = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)


class CreateConsentSerializer(serializers.Serializer):
    provider = serializers.CharField(max_length=120)
    scopes = serializers.ListField(
        child=serializers.CharField(),
        min_length=1
    )
    expiration_days = serializers.IntegerField(default=90, min_value=1, max_value=365)
    user_id = serializers.IntegerField(required=False, default=1)


class ConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consent
        fields = "__all__"
        read_only_fields = ('created_at',)


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = "__all__"


class LinkBankAccountSerializer(serializers.Serializer):
    consent_id = serializers.IntegerField()
    institution = serializers.CharField(max_length=120)
    account_id = serializers.CharField(max_length=120)
    branch = serializers.CharField(max_length=16, required=False, allow_blank=True)
    number = serializers.CharField(max_length=32, required=False, allow_blank=True)
    ispb = serializers.CharField(max_length=8, required=False, allow_blank=True)


class ReconcilePaymentSerializer(serializers.Serializer):
    consent_id = serializers.IntegerField()
    account_id = serializers.CharField(max_length=120)
    expected_amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    expected_txid = serializers.CharField(max_length=120, required=False, allow_blank=True)
    user_id = serializers.IntegerField(required=False, default=1)
