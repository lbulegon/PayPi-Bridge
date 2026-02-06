"""
Tests for PayPiBridge views.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from app.paypibridge.models import PaymentIntent, Consent

User = get_user_model()


class IntentViewTest(TestCase):
    """Tests for IntentView."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_intent(self):
        """Test creating a PaymentIntent."""
        url = reverse('create-intent')
        data = {
            'payee_user_id': self.user.id,
            'amount_pi': '10.5',
            'metadata': {'order_id': '123'}
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('intent_id', response.data)
        self.assertIn('amount_pi', response.data)
        
        # Verify intent was created in database
        intent = PaymentIntent.objects.get(intent_id=response.data['intent_id'])
        self.assertEqual(intent.amount_pi, Decimal('10.5'))
        self.assertEqual(intent.status, 'CREATED')
    
    def test_create_intent_invalid_data(self):
        """Test creating intent with invalid data."""
        url = reverse('create-intent')
        data = {
            'payee_user_id': 'invalid',
            'amount_pi': 'not-a-number'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_intent_payee_user_not_found(self):
        """Test creating intent with non-existent payee_user_id returns 400."""
        url = reverse('create-intent')
        data = {
            'payee_user_id': 99999,
            'amount_pi': '10.5',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('payee_user_id', response.data)

    def test_create_intent_without_auth(self):
        """Test creating intent without authentication (AllowAny)."""
        self.client.force_authenticate(user=None)
        url = reverse('create-intent')
        data = {
            'payee_user_id': self.user.id,
            'amount_pi': '5.0',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('intent_id', response.data)


class IntentListViewTest(TestCase):
    """Tests for IntentListView (GET /api/intents)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_intent_list_returns_list(self):
        """GET /api/intents returns 200 and list of intents."""
        PaymentIntent.objects.create(
            intent_id="pi_111",
            payer_address="addr1",
            payee_user=self.user,
            amount_pi=Decimal("10"),
            status="CREATED"
        )
        url = reverse('list-intents')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['intent_id'], 'pi_111')
        self.assertEqual(response.data[0]['status'], 'CREATED')

    def test_intent_list_empty(self):
        """GET /api/intents with no intents returns empty list."""
        url = reverse('list-intents')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class VerifyPiPaymentViewTest(TestCase):
    """Tests for VerifyPiPaymentView (POST /api/payments/verify)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.intent = PaymentIntent.objects.create(
            intent_id="pi_verify_test",
            payer_address="onchain_tbd",
            payee_user=self.user,
            amount_pi=Decimal("10"),
            status="CREATED"
        )

    def test_verify_intent_not_found(self):
        """POST verify with non-existent intent_id returns 404."""
        from unittest.mock import patch, MagicMock
        mock_payment = {
            'from_address': 'GXXX',
            'status': {'cancelled': False, 'user_cancelled': False, 'transaction_verified': True},
            'transaction': {'txid': 'tx123'},
        }
        with patch('app.paypibridge.views.get_pi_service') as m:
            m.return_value.is_available.return_value = True
            m.return_value.verify_payment.return_value = mock_payment
            url = reverse('verify-payment')
            response = self.client.post(url, {
                'payment_id': 'pay_abc',
                'intent_id': 'pi_nonexistent',
            }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('PaymentIntent not found', response.data['detail'])

    def test_verify_invalid_serializer(self):
        """POST verify with missing fields returns 400."""
        url = reverse('verify-payment')
        response = self.client.post(url, {'payment_id': 'x'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CCIPWebhookViewTest(TestCase):
    """Tests for CCIPWebhookView."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.intent = PaymentIntent.objects.create(
            intent_id="pi_1234567890",
            payer_address="GABC123...",
            payee_user=self.user,
            amount_pi=Decimal("10.5"),
            status="CREATED"
        )
    
    def test_ccip_webhook_no_secret(self):
        """Test webhook when CCIP_WEBHOOK_SECRET is not set returns 503."""
        with patch.dict(os.environ, {"CCIP_WEBHOOK_SECRET": ""}, clear=False):
            url = reverse('ccip-webhook')
            response = self.client.post(url, {"intent_id": self.intent.intent_id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_ccip_webhook_invalid_signature(self):
        """Test webhook with invalid signature returns 403."""
        with patch.dict(os.environ, {"CCIP_WEBHOOK_SECRET": "test-secret"}, clear=False):
            url = reverse('ccip-webhook')
            data = {'intent_id': self.intent.intent_id, 'fx_quote': {'brl_amount': '50.00'}}
            response = self.client.post(
                url, data, format='json',
                HTTP_X_SIGNATURE='invalid-sig'
            )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ccip_webhook_intent_not_found(self):
        """Test webhook with non-existent intent returns 404 (with valid HMAC)."""
        secret = "test-secret"
        body = json.dumps({"intent_id": "nonexistent", "fx_quote": {"brl_amount": "50.00"}}, separators=(",", ":"))
        sig = _ccip_sign(body.encode(), secret)
        with patch.dict(os.environ, {"CCIP_WEBHOOK_SECRET": secret}, clear=False):
            url = reverse('ccip-webhook')
            response = self.client.post(
                url, body, content_type='application/json',
                HTTP_X_SIGNATURE=sig
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_ccip_webhook_valid_updates_intent(self):
        """Test webhook with valid HMAC updates PaymentIntent."""
        secret = "test-secret"
        data = {
            "intent_id": self.intent.intent_id,
            "event_id": "evt_001",
            "fx_quote": {"brl_amount": "50.00"},
            "status": "CONFIRMED",
        }
        body = json.dumps(data, separators=(",", ":"))
        sig = _ccip_sign(body.encode(), secret)
        with patch.dict(os.environ, {"CCIP_WEBHOOK_SECRET": secret}, clear=False):
            url = reverse('ccip-webhook')
            response = self.client.post(
                url, body, content_type='application/json',
                HTTP_X_SIGNATURE=sig
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("ok"), True)
        self.intent.refresh_from_db()
        self.assertEqual(self.intent.status, "CONFIRMED")
        self.assertEqual(str(self.intent.amount_brl), "50.00")
        self.assertTrue(WebhookEvent.objects.filter(intent_id=self.intent.intent_id, event_id="evt_001").exists())

    def test_ccip_webhook_idempotency(self):
        """Test same event_id twice returns 200 and already_processed on second call."""
        secret = "test-secret"
        data = {
            "intent_id": self.intent.intent_id,
            "event_id": "evt_idem",
            "fx_quote": {"brl_amount": "25.00"},
            "status": "CONFIRMED",
        }
        body = json.dumps(data, separators=(",", ":"))
        sig = _ccip_sign(body.encode(), secret)
        with patch.dict(os.environ, {"CCIP_WEBHOOK_SECRET": secret}, clear=False):
            url = reverse('ccip-webhook')
            r1 = self.client.post(url, body, content_type='application/json', HTTP_X_SIGNATURE=sig)
            r2 = self.client.post(url, body, content_type='application/json', HTTP_X_SIGNATURE=sig)
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertIsNone(r1.data.get("already_processed"))
        self.assertTrue(r2.data.get("already_processed"))
        self.intent.refresh_from_db()
        self.assertEqual(str(self.intent.amount_brl), "25.00")

    def test_ccip_webhook_missing_intent_id(self):
        """Test webhook without intent_id returns 400."""
        secret = "test-secret"
        body = json.dumps({"fx_quote": {}}, separators=(",", ":"))
        sig = _ccip_sign(body.encode(), secret)
        with patch.dict(os.environ, {"CCIP_WEBHOOK_SECRET": secret}, clear=False):
            url = reverse('ccip-webhook')
            response = self.client.post(
                url, body, content_type='application/json',
                HTTP_X_SIGNATURE=sig
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PixPayoutViewTest(TestCase):
    """Tests for PixPayoutView."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create consent
        self.consent = Consent.objects.create(
            user=self.user,
            provider="bank_example",
            scope={"payments": "write"},
            consent_id="consent_123",
            status="ACTIVE"
        )
    
    def test_pix_payout_no_consent(self):
        """Test payout without active consent."""
        url = reverse('pix-payout')
        data = {
            'payee_user_id': self.user.id,
            'amount_brl': '50.00',
            'cpf': '12345678901',
            'pix_key': 'test@example.com'
        }
        
        # Delete consent
        self.consent.delete()
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no active consent', response.data['detail'])
