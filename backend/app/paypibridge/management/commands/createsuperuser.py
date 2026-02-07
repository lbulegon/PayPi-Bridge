"""
Comando Django para criar superusuário de forma não-interativa.
Útil para ambientes de produção/deploy (Railway, Heroku, etc.).

Uso:
    python manage.py createsuperuser --username admin --email admin@example.com --password senha123
    python manage.py createsuperuser --username admin --email admin@example.com --password senha123 --no-input
"""
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    help = 'Cria um superusuário de forma não-interativa'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Nome de usuário do superusuário',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email do superusuário',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Senha do superusuário',
        )
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Não solicitar confirmação',
        )
        parser.add_argument(
            '--skip-if-exists',
            action='store_true',
            help='Pular criação se o usuário já existir',
        )

    def handle(self, *args, **options):
        username = options.get('username') or os.getenv('DJANGO_SUPERUSER_USERNAME')
        email = options.get('email') or os.getenv('DJANGO_SUPERUSER_EMAIL')
        password = options.get('password') or os.getenv('DJANGO_SUPERUSER_PASSWORD')
        no_input = options.get('no_input', False)
        skip_if_exists = options.get('skip_if_exists', False)

        # Se não fornecido via argumentos ou env vars, solicitar interativamente
        if not username:
            username = input('Username: ')
        if not email:
            email = input('Email: ')
        if not password:
            password = input('Password: ')
            password_confirm = input('Password (again): ')
            if password != password_confirm:
                raise CommandError('As senhas não coincidem!')

        # Validar campos obrigatórios
        if not username:
            raise CommandError('Username é obrigatório')
        if not email:
            raise CommandError('Email é obrigatório')
        if not password:
            raise CommandError('Password é obrigatório')

        # Verificar se o usuário já existe
        if User.objects.filter(username=username).exists():
            if skip_if_exists:
                self.stdout.write(
                    self.style.WARNING(f'Usuário "{username}" já existe. Pulando criação.')
                )
                return
            else:
                raise CommandError(f'Usuário "{username}" já existe!')

        # Criar superusuário
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Superusuário "{username}" criado com sucesso!'
                )
            )
            self.stdout.write(f'  Username: {user.username}')
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  ID: {user.id}')
            
        except IntegrityError as e:
            raise CommandError(f'Erro ao criar usuário: {e}')
        except Exception as e:
            raise CommandError(f'Erro inesperado: {e}')
