"""OpenPix client e SettlementPixPort com PIX_PROVIDER=openpix."""
import os
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from app.paypibridge.models import Consent
from app.paypibridge.services.settlement_pix_port import SettlementPixPort

User = get_user_model()


class OpenPixSettlementPortTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", email="u1@t.com", password="x")
        self.consent = Consent.objects.create(
            user=self.user,
            provider="mock",
            scope={},
            consent_id="c_op_1",
            status="ACTIVE",
        )

    @patch.dict(
        os.environ,
        {
            "PIX_PROVIDER": "openpix",
            "OPENPIX_APP_ID": "app_test_123",
            "OPENPIX_FROM_PIX_KEY": "origem@openpix.test",
            "OPENPIX_BASE_URL": "https://api.openpix.com.br/api/v1",
            "OF_USE_MOCK": "true",
        },
        clear=False,
    )
    @patch("app.paypibridge.clients.openpix.requests.post")
    def test_settlement_uses_openpix_transfer(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"{}"
        mock_resp.json.return_value = {
            "transaction": {
                "correlationID": "corr-test-uuid",
                "value": 4760,
            }
        }
        mock_post.return_value = mock_resp

        port = SettlementPixPort()
        out = port.send(
            consent=self.consent,
            cpf="12345678901",
            pix_key="destino@email.com",
            amount_brl=Decimal("47.60"),
            description="test",
        )

        self.assertTrue(out.get("success"))
        self.assertEqual(out.get("txid"), "corr-test-uuid")
        self.assertEqual(out.get("provider"), "openpix")
        mock_post.assert_called_once()
        call_kw = mock_post.call_args
        self.assertIn("/transfer", call_kw[0][0])
        body = call_kw[1]["json"]
        self.assertEqual(body["value"], 4760)
        self.assertEqual(body["fromPixKey"], "origem@openpix.test")
        self.assertEqual(body["toPixKey"], "destino@email.com")

    @patch.dict(os.environ, {"PIX_PROVIDER": "openpix"}, clear=False)
    def test_openpix_missing_config_returns_error(self):
        port = SettlementPixPort()
        out = port.send(
            consent=self.consent,
            cpf="12345678901",
            pix_key="x@y.com",
            amount_brl=Decimal("10.00"),
        )
        self.assertFalse(out.get("success"))
        self.assertEqual(out.get("error"), "openpix_not_configured")
