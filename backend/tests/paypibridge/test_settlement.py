"""Tests for settlement engine."""
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from app.paypibridge.models import PaymentIntent, Consent

User = get_user_model()


class SettlementExecuteAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="u1",
            email="u1@example.com",
            password="x",
        )
        self.consent = Consent.objects.create(
            user=self.user,
            provider="mock",
            scope={},
            consent_id="c_settle_1",
            status="ACTIVE",
        )
        self.intent = PaymentIntent.objects.create(
            intent_id="pi_settle_1",
            payer_address="GXXX",
            payee_user=self.user,
            amount_pi=Decimal("10"),
            verified_at=timezone.now(),
            status="CREATED",
        )

    @patch("app.paypibridge.services.settlement_pix_port._of_mock", return_value=True)
    @patch("app.paypibridge.services.settlement_service.get_pricing_service")
    def test_settlement_execute_success_mock_pix(self, mock_pricing, _mock_of):
        pr = MagicMock()
        pr.convert_pi_to_brl.return_value = Decimal("47.60")
        mock_pricing.return_value = pr

        url = reverse("settlement-execute")
        r = self.client.post(
            url,
            {
                "intent_id": "pi_settle_1",
                "cpf": "12345678901",
                "pix_key": "test@example.com",
                "description": "test",
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["status"], "SETTLED")
        self.intent.refresh_from_db()
        self.assertEqual(self.intent.status, "SETTLED")
        self.assertEqual(self.intent.settlement_status, "SETTLED")
        self.assertIsNotNone(self.intent.settlement_pix_txid)

    def test_settlement_rejects_without_verified_at(self):
        self.intent.verified_at = None
        self.intent.save(update_fields=["verified_at"])

        url = reverse("settlement-execute")
        r = self.client.post(
            url,
            {
                "intent_id": "pi_settle_1",
                "cpf": "12345678901",
                "pix_key": "x@y.com",
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("pi_payment_not_verified", r.data.get("detail", ""))
