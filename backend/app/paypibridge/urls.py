from django.urls import path
from .views import (
    IntentView, IntentListView, CCIPWebhookView, PixPayoutView,
    VerifyPiPaymentView, PiBalanceView, PiStatusView,
    ConsentView, ConsentDetailView,
    LinkBankAccountView, ReconcilePaymentView,
    FXQuoteView, RelayerStatusView,
    PiNetworkWebhookView, HealthCheckView, TestEndpointsView,
    AdminStatsView, AdminIntentsView
)

urlpatterns = [
    # PaymentIntent
    path("checkout/pi-intent", IntentView.as_view(), name="create-intent"),
    path("intents", IntentListView.as_view(), name="list-intents"),
    path("payments/verify", VerifyPiPaymentView.as_view(), name="verify-payment"),
    
    # Webhooks
    path("webhooks/ccip", CCIPWebhookView.as_view(), name="ccip-webhook"),
    path("webhooks/pi", PiNetworkWebhookView.as_view(), name="pi-webhook"),
    
    # Relayer
    path("relayer/status", RelayerStatusView.as_view(), name="relayer-status"),
    
    # Health & Testing
    path("health", HealthCheckView.as_view(), name="health-check"),
    path("test", TestEndpointsView.as_view(), name="test-endpoints"),
    
    # Admin & Monitoring
    path("admin/stats", AdminStatsView.as_view(), name="admin-stats"),
    path("admin/intents", AdminIntentsView.as_view(), name="admin-intents"),
    
    # Payouts
    path("payouts/pix", PixPayoutView.as_view(), name="pix-payout"),
    
    # Pi Network
    path("pi/status", PiStatusView.as_view(), name="pi-status"),
    path("pi/balance", PiBalanceView.as_view(), name="pi-balance"),
    
    # FX / Taxa de Câmbio
    path("fx/quote", FXQuoteView.as_view(), name="fx-quote"),
    
    # Open Finance - Consent Management
    path("consents", ConsentView.as_view(), name="consents-list"),
    path("consents/<int:consent_id>", ConsentDetailView.as_view(), name="consent-detail"),
    
    # Open Finance - Bank Accounts
    path("bank-accounts/link", LinkBankAccountView.as_view(), name="link-bank-account"),
    
    # Open Finance - Reconciliation
    path("reconcile", ReconcilePaymentView.as_view(), name="reconcile-payment"),
]
