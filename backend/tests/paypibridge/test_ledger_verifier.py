"""Tests for Horizon ledger verification helper."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase

from app.paypibridge.services.ledger_verifier import LedgerVerifier


class LedgerVerifierTest(TestCase):
    def test_verify_transaction_not_found(self):
        with patch("app.paypibridge.services.ledger_verifier.requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=404)
            v = LedgerVerifier("https://example.com", timeout=2)
            r = v.verify_transaction("deadbeef")
        self.assertFalse(r.found)
        self.assertIn("http_404", r.raw_error or "")

    def test_verify_transaction_success_payment_op(self):
        tx_json = {
            "memo": "m",
            "source_account": "GAAA",
            "created_at": "2020-01-01T00:00:00Z",
        }
        ops_json = {
            "_embedded": {
                "records": [
                    {"type": "payment", "amount": "3.5", "to": "GBBB"},
                ]
            }
        }

        def side_effect(url, timeout=None):
            m = MagicMock()
            m.status_code = 200
            if url.endswith("/operations"):
                m.json.return_value = ops_json
            else:
                m.json.return_value = tx_json
            return m

        with patch(
            "app.paypibridge.services.ledger_verifier.requests.get", side_effect=side_effect
        ):
            v = LedgerVerifier("https://h.example", timeout=2)
            r = v.verify_transaction("abc123")

        self.assertTrue(r.found)
        self.assertEqual(r.amount, Decimal("3.5"))
        self.assertEqual(r.destination, "GBBB")
        self.assertEqual(r.memo, "m")
