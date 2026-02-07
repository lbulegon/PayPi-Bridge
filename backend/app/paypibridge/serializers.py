from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import PaymentIntent, PixTransaction, Consent, BankAccount

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer para registro de novos usuários."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password_confirm', 'first_name', 'last_name')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate_email(self, value):
        """Valida que email é único."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email já está em uso.")
        return value
    
    def validate_username(self, value):
        """Valida que username é único."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este username já está em uso.")
        return value
    
    def validate(self, attrs):
        """Valida que as senhas coincidem."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "As senhas não coincidem."
            })
        return attrs
    
    def create(self, validated_data):
        """Cria novo usuário."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer para dados do usuário."""
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'is_active')
        read_only_fields = ('id', 'date_joined', 'is_active')


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer customizado para tokens JWT com dados adicionais do usuário."""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Adicionar claims customizados
        token['username'] = user.username
        token['email'] = user.email
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        # Adicionar dados do usuário na resposta
        data['user'] = UserSerializer(self.user).data
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para alteração de senha."""
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_new_password_confirm(self, value):
        """Valida que as novas senhas coincidem."""
        if self.initial_data.get('new_password') != value:
            raise serializers.ValidationError("As novas senhas não coincidem.")
        return value
    
    def validate_old_password(self, value):
        """Valida que a senha antiga está correta."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Senha atual incorreta.")
        return value


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
