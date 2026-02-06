"""
Tests for Open Finance integration.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from app.paypibridge.models import Consent, BankAccount
from app.paypibridge.clients.open_finance import OpenFinanceClient
from app.paypibridge.services.consent_service import ConsentService

User = get_user_model()


class OpenFinanceClientTest(TestCase):
    """Tests for OpenFinanceClient."""
    
    def setUp(self):
        self.client = OpenFinanceClient(
            base_url="https://api.openbanking.sandbox.example.com",
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
    
    @patch('app.paypibridge.clients.open_finance.requests.Session.post')
    def test_get_access_token(self, mock_post):
        """Test OAuth2 token acquisition."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_token_123",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        token = self.client._get_access_token()
        
        self.assertEqual(token, "test_token_123")
        self.assertEqual(self.client._access_token, "test_token_123")
    
    @patch('app.paypibridge.clients.open_finance.requests.Session.post')
    def test_create_consent(self, mock_post):
        """Test consent creation."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "consentId": "consent_123",
                "status": "AWAITING_AUTHORISATION"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Mock token first
        self.client._access_token = "test_token"
        self.client._token_expires_at = None
        
        consent_data = self.client.create_consent(
            user_id="user_123",
            scopes=["payments", "accounts"]
        )
        
        self.assertIsNotNone(consent_data)
        self.assertEqual(consent_data["data"]["consentId"], "consent_123")
    
    @patch('app.paypibridge.clients.open_finance.requests.Session.post')
    def test_create_pix_payment(self, mock_post):
        """Test Pix payment creation."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "payment": {
                    "paymentId": "E2E123456789",
                    "status": "PENDING",
                    "amount": "100.00",
                    "currency": "BRL"
                }
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Mock token
        self.client._access_token = "test_token"
        self.client._token_expires_at = None
        
        result = self.client.create_pix_payment(
            consent_id="consent_123",
            cpf="12345678901",
            pix_key="test@example.com",
            amount_brl="100.00",
            description="Test payment"
        )
        
        self.assertEqual(result["txid"], "E2E123456789")
        self.assertEqual(result["status"], "PENDING")
        self.assertEqual(result["amount"], "100.00")


class ConsentServiceTest(TestCase):
    """Tests for ConsentService."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = ConsentService()
    
    @patch('app.paypibridge.services.consent_service.OpenFinanceClient.create_consent')
    def test_create_consent(self, mock_create):
        """Test consent creation via service."""
        mock_create.return_value = {
            "data": {
                "consentId": "consent_123"
            }
        }
        
        consent = self.service.create_consent(
            user=self.user,
            provider="bank_example",
            scopes=["payments", "accounts"]
        )
        
        self.assertIsNotNone(consent)
        self.assertEqual(consent.consent_id, "consent_123")
        self.assertEqual(consent.user, self.user)
        self.assertEqual(consent.provider, "bank_example")
        self.assertEqual(consent.status, "ACTIVE")
    
    def test_validate_consent_active(self):
        """Test consent validation for active consent."""
        consent = Consent.objects.create(
            user=self.user,
            provider="bank_example",
            scope={"scopes": ["payments"]},
            consent_id="consent_123",
            status="ACTIVE"
        )
        
        # Mock refresh to not fail
        with patch.object(self.service, 'refresh_consent', return_value=True):
            is_valid = self.service.validate_consent(consent)
            self.assertTrue(is_valid)
    
    def test_get_active_consent(self):
        """Test getting active consent."""
        consent = Consent.objects.create(
            user=self.user,
            provider="bank_example",
            scope={"scopes": ["payments"]},
            consent_id="consent_123",
            status="ACTIVE"
        )
        
        with patch.object(self.service, 'validate_consent', return_value=True):
            active_consent = self.service.get_active_consent(self.user)
            self.assertIsNotNone(active_consent)
            self.assertEqual(active_consent.id, consent.id)
