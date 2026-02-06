"""
Cria usuário de teste para checkout (payee_user_id).
Uso: python manage.py createtestuser
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Cria usuário de teste para uso no checkout (payee_user_id=1 ou próximo id)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default="test",
            help="Username do usuário de teste (default: test)",
        )
        parser.add_argument(
            "--password",
            default="test",
            help="Senha do usuário de teste (default: test)",
        )
        parser.add_argument(
            "--email",
            default="test@paypibridge.local",
            help="Email do usuário de teste",
        )

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        email = options["email"]

        if User.objects.filter(username=username).exists():
            u = User.objects.get(username=username)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Usuário '{username}' já existe (id={u.id}). Use payee_user_id={u.id} no checkout."
                )
            )
            return

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Usuário de teste criado: username={username}, id={user.id}. "
                f"Use payee_user_id={user.id} no POST /api/checkout/pi-intent."
            )
        )
