from django.urls import path
from .views import IntentView, CCIPWebhookView, PixPayoutView

urlpatterns = [
    path("checkout/pi-intent", IntentView.as_view()),
    path("webhooks/ccip", CCIPWebhookView.as_view()),
    path("payouts/pix", PixPayoutView.as_view()),
]
