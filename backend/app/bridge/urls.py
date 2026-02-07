"""
URLs do PPBridge Service.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api.views import BridgeFlowViewSet, WebhookTestView

router = DefaultRouter()
router.register(r'flows', BridgeFlowViewSet, basename='bridge-flow')
router.register(r'webhooks', WebhookTestView, basename='webhook-test')

urlpatterns = [
    path('', include(router.urls)),
]
