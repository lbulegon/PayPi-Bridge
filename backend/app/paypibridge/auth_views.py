"""
Views de autenticação para PayPi-Bridge.
"""
import logging
from rest_framework import status, views, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    Registro de novo usuário.
    
    POST /api/auth/register/
    Body: username, email, password, password_confirm, first_name (opcional), last_name (opcional)
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    
    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = serializer.save()
            
            logger.info(
                f"User registered successfully",
                extra={'user_id': user.id, 'username': user.username, 'email': user.email}
            )
            
            # Gerar tokens JWT para o novo usuário
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Usuário criado com sucesso',
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'redirect_url': '/dashboard/',
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(
                f"Error registering user: {str(e)}",
                exc_info=True,
                extra={'username': request.data.get('username')}
            )
            return Response(
                {
                    'code': 'REGISTRATION_ERROR',
                    'message': 'Erro ao criar usuário',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView(TokenObtainPairView):
    """
    Login e obtenção de tokens JWT.
    
    POST /api/auth/login/
    Body: username (ou email), password
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        # Permitir login com email ou username
        username_or_email = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')
        
        if not username_or_email or not password:
            return Response(
                {
                    'code': 'MISSING_CREDENTIALS',
                    'message': 'Username/email e senha são obrigatórios',
                    'detail': 'Forneça username (ou email) e password'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Tentar encontrar usuário por email ou username
        try:
            if '@' in username_or_email:
                user = User.objects.get(email=username_or_email)
            else:
                user = User.objects.get(username=username_or_email)
        except User.DoesNotExist:
            logger.warning(
                f"Login attempt with invalid credentials",
                extra={'username_or_email': username_or_email}
            )
            return Response(
                {
                    'code': 'INVALID_CREDENTIALS',
                    'message': 'Credenciais inválidas',
                    'detail': 'Username/email ou senha incorretos'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verificar senha
        if not user.check_password(password):
            logger.warning(
                f"Login attempt with wrong password",
                extra={'user_id': user.id, 'username': user.username}
            )
            return Response(
                {
                    'code': 'INVALID_CREDENTIALS',
                    'message': 'Credenciais inválidas',
                    'detail': 'Username/email ou senha incorretos'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verificar se usuário está ativo
        if not user.is_active:
            logger.warning(
                f"Login attempt with inactive user",
                extra={'user_id': user.id, 'username': user.username}
            )
            return Response(
                {
                    'code': 'USER_INACTIVE',
                    'message': 'Usuário inativo',
                    'detail': 'Sua conta foi desativada. Entre em contato com o suporte.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Gerar tokens
        refresh = RefreshToken.for_user(user)
        
        logger.info(
            f"User logged in successfully",
            extra={'user_id': user.id, 'username': user.username}
        )
        
        return Response({
            'message': 'Login realizado com sucesso',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'redirect_url': '/dashboard/',
        }, status=status.HTTP_200_OK)


class RefreshTokenView(TokenRefreshView):
    """
    Refresh de access token.
    
    POST /api/auth/refresh/
    Body: refresh (refresh token)
    """
    permission_classes = [AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='30/m', method='POST'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class LogoutView(views.APIView):
    """
    Logout e invalidação de refresh token.
    
    POST /api/auth/logout/
    Body: refresh (refresh token a ser invalidado)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response(
                    {
                        'code': 'MISSING_TOKEN',
                        'message': 'Refresh token é obrigatório',
                        'detail': 'Forneça o refresh token no body'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            logger.info(
                f"User logged out successfully",
                extra={'user_id': request.user.id, 'username': request.user.username}
            )
            
            return Response({
                'message': 'Logout realizado com sucesso'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(
                f"Error during logout: {str(e)}",
                exc_info=True,
                extra={'user_id': request.user.id}
            )
            return Response(
                {
                    'code': 'LOGOUT_ERROR',
                    'message': 'Erro ao fazer logout',
                    'detail': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Obter e atualizar perfil do usuário autenticado.
    
    GET /api/auth/me/ - Obter perfil
    PUT /api/auth/me/ - Atualizar perfil
    PATCH /api/auth/me/ - Atualizar perfil (parcial)
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Não permitir alterar email se já existe outro usuário com esse email
        if 'email' in serializer.validated_data:
            email = serializer.validated_data['email']
            if User.objects.filter(email=email).exclude(id=instance.id).exists():
                return Response(
                    {
                        'code': 'EMAIL_ALREADY_EXISTS',
                        'message': 'Este email já está em uso',
                        'detail': f'Outro usuário já possui o email {email}'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        self.perform_update(serializer)
        
        logger.info(
            f"User profile updated",
            extra={'user_id': instance.id, 'username': instance.username}
        )
        
        return Response(serializer.data)


class ChangePasswordView(views.APIView):
    """
    Alterar senha do usuário autenticado.
    
    POST /api/auth/change-password/
    Body: old_password, new_password, new_password_confirm
    """
    permission_classes = [IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='5/m', method='POST'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        logger.info(
            f"User password changed",
            extra={'user_id': user.id, 'username': user.username}
        )
        
        return Response({
            'message': 'Senha alterada com sucesso'
        }, status=status.HTTP_200_OK)


class CheckAuthView(views.APIView):
    """
    Verificar se usuário está autenticado e obter dados do usuário.
    
    GET /api/auth/check/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'authenticated': True,
            'user': UserSerializer(request.user).data
        })
