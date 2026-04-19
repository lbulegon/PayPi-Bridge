"""Multi-tenant ledger, wallet e taxas (v2)."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from app.paypibridge.models import LedgerEntry, PaymentIntent, Tenant, Wallet
from app.paypibridge.services.ledger_service import (
    apply_ledger_entry,
    credit_pi_for_verified_intent,
    ensure_wallet,
    get_platform_tenant,
)

User = get_user_model()


class LedgerServiceTest(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Loja Teste",
            slug="loja-teste",
            api_key="lk_test_12345678",
            webhook_url="",
        )

    def test_ensure_wallet_creates_pair(self):
        w = ensure_wallet(self.tenant, Wallet.ASSET_PI)
        self.assertEqual(w.asset, "PI")
        self.assertEqual(w.balance, Decimal("0"))

    def test_apply_ledger_credit_debit_idempotent(self):
        apply_ledger_entry(
            self.tenant,
            Wallet.ASSET_PI,
            Decimal("10"),
            LedgerEntry.ENTRY_CREDIT,
            "ref-1",
            idempotency_key="idem:1",
        )
        apply_ledger_entry(
            self.tenant,
            Wallet.ASSET_PI,
            Decimal("10"),
            LedgerEntry.ENTRY_CREDIT,
            "ref-1",
            idempotency_key="idem:1",
        )
        w = ensure_wallet(self.tenant, Wallet.ASSET_PI)
        self.assertEqual(w.balance, Decimal("10"))
        self.assertEqual(LedgerEntry.objects.filter(idempotency_key="idem:1").count(), 1)

    def test_credit_pi_for_verified_intent_skips_without_tenant(self):
        u = User.objects.create_user(username="u1", email="u1@t.com", password="x")
        intent = PaymentIntent.objects.create(
            intent_id="pi_no_tenant",
            payer_address="x",
            payee_user=u,
            amount_pi=Decimal("5"),
        )
        self.assertIsNone(credit_pi_for_verified_intent(intent))

    def test_credit_pi_for_verified_intent_with_tenant(self):
        u = User.objects.create_user(username="u2", email="u2@t.com", password="x")
        intent = PaymentIntent.objects.create(
            intent_id="pi_with_tenant",
            payer_address="x",
            payee_user=u,
            amount_pi=Decimal("3.5"),
            tenant=self.tenant,
        )
        credit_pi_for_verified_intent(intent)
        w = ensure_wallet(self.tenant, Wallet.ASSET_PI)
        self.assertEqual(w.balance, Decimal("3.5"))


class TenantApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="u3", email="u3@t.com", password="x")
        self.tenant = Tenant.objects.create(
            name="API Client",
            slug="api-client",
            api_key="valid_key_abc",
            webhook_url="",
        )

    def test_create_intent_invalid_tenant_key_returns_401(self):
        url = reverse("create-intent")
        r = self.client.post(
            url,
            {
                "payee_user_id": self.user.id,
                "amount_pi": "1",
                "tenant_api_key": "wrong",
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tenant_wallets_requires_header(self):
        url = reverse("tenant-wallets")
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tenant_wallets_ok(self):
        url = reverse("tenant-wallets")
        r = self.client.get(url, HTTP_X_PAYPI_TENANT_KEY="valid_key_abc")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["tenant_slug"], "api-client")
        self.assertEqual(len(r.data["wallets"]), 2)

    def test_platform_tenant_seeded(self):
        p = get_platform_tenant()
        self.assertIsNotNone(p)
        self.assertTrue(p.is_platform)
