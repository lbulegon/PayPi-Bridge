from rest_framework import serializers
from .models import PaymentIntent, PixTransaction, Consent, BankAccount

class CreateIntentSerializer(serializers.Serializer):
    payee_user_id = serializers.IntegerField()
    amount_pi = serializers.DecimalField(max_digits=20, decimal_places=8)
    metadata = serializers.DictField(required=False)

class PaymentIntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentIntent
        fields = "__all__"

class PixPayoutSerializer(serializers.Serializer):
    payee_user_id = serializers.IntegerField()
    amount_brl = serializers.DecimalField(max_digits=20, decimal_places=2)
    cpf = serializers.CharField()
    pix_key = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)

class ConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consent
        fields = "__all__"

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = "__all__"
