from django.apps import AppConfig


class PayPiBridgeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.paypibridge"
    
    def ready(self):
        """Import tasks when app is ready."""
        import app.paypibridge.tasks  # noqa