"""
Unit tests for PiService with mocks.
"""
import os
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from django.test import TestCase

from app.paypibridge.services.pi_service import PiService, get_pi_service


class PiServiceTest(TestCase):
    """Tests for PiService with mocked Pi Network SDK."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pi_service = PiService()
        self.mock_pi_client = MagicMock()
    
    @patch.dict(os.environ, {
        'PI_API_KEY': 'test-api-key',
        'PI_WALLET_PRIVATE_SEED': 'test-seed',
        'PI_NETWORK': 'Pi Testnet'
    }, clear=False)
    @patch('app.paypibridge.services.pi_service.PiNetwork')
    def test_is_available_with_credentials(self, mock_pi_network_class):
        """Test is_available returns True when credentials are configured."""
        mock_pi_network_class.return_value = self.mock_pi_client
        self.pi_service._pi_client = None  # Reset singleton
        
        result = self.pi_service.is_available()
        
        self.assertTrue(result)
        mock_pi_network_class.assert_called_once()
    
    @patch.dict(os.environ, {
        'PI_API_KEY': '',
        'PI_WALLET_PRIVATE_SEED': '',
    }, clear=False)
    def test_is_available_without_credentials(self):
        """Test is_available returns False when credentials are missing."""
        self.pi_service._pi_client = None
        
        result = self.pi_service.is_available()
        
        self.assertFalse(result)
    
    @patch.dict(os.environ, {
        'PI_API_KEY': 'test-api-key',
        'PI_WALLET_PRIVATE_SEED': 'test-seed',
        'PI_NETWORK': 'Pi Testnet'
    }, clear=False)
    @patch('app.paypibridge.services.pi_service.PiNetwork')
    def test_get_balance_success(self, mock_pi_network_class):
        """Test get_balance returns balance when available."""
        mock_client = MagicMock()
        mock_client.get_balance.return_value = 100.5
        mock_pi_network_class.return_value = mock_client
        self.pi_service._pi_client = mock_client
        
        result = self.pi_service.get_balance()
        
        self.assertEqual(result, Decimal('100.5'))
        mock_client.get_balance.assert_called_once()
    
    @patch.dict(os.environ, {
        'PI_API_KEY': '',
        'PI_WALLET_PRIVATE_SEED': '',
    }, clear=False)
    def test_get_balance_unavailable(self):
        """Test get_balance returns None when Pi Network is unavailable."""
        self.pi_service._pi_client = None
        
        result = self.pi_service.get_balance()
        
        self.assertIsNone(result)
    
    @patch.dict(os.environ, {
        'PI_API_KEY': 'test-api-key',
        'PI_WALLET_PRIVATE_SEED': 'test-seed',
    }, clear=False)
    @patch('app.paypibridge.services.pi_service.PiNetwork')
    def test_get_balance_exception(self, mock_pi_network_class):
        """Test get_balance handles exceptions gracefully."""
        mock_client = MagicMock()
        mock_client.get_balance.side_effect = Exception("Network error")
        mock_pi_network_class.return_value = mock_client
        self.pi_service._pi_client = mock_client
        
        result = self.pi_service.get_balance()
        
        self.assertIsNone(result)
    
    @patch.dict(os.environ, {
        'PI_API_KEY': 'test-api-key',
        'PI_WALLET_PRIVATE_SEED': 'test-seed',
    }, clear=False)
    @patch('app.paypibridge.services.pi_service.PiNetwork')
    def test_verify_payment_success(self, mock_pi_network_class):
        """Test verify_payment returns payment data when valid."""
        mock_client = MagicMock()
        mock_payment = {
            'id': 'payment_123',
            'from_address': 'GABC123...',
            'to_address': 'GDEF456...',
            'amount': 10.5,
            'status': {'transaction_verified': True}
        }
        mock_client.get_payment.return_value = mock_payment
        mock_pi_network_class.return_value = mock_client
        self.pi_service._pi_client = mock_client
        
        result = self.pi_service.verify_payment('payment_123')
        
        self.assertEqual(result, mock_payment)
        mock_client.get_payment.assert_called_once_with('payment_123')
    
    @patch.dict(os.environ, {
        'PI_API_KEY': 'test-api-key',
        'PI_WALLET_PRIVATE_SEED': 'test-seed',
    }, clear=False)
    @patch('app.paypibridge.services.pi_service.PiNetwork')
    def test_verify_payment_not_found(self, mock_pi_network_class):
        """Test verify_payment returns None when payment not found."""
        mock_client = MagicMock()
        mock_client.get_payment.return_value = {'error': 'not_found'}
        mock_pi_network_class.return_value = mock_client
        self.pi_service._pi_client = mock_client
        
        result = self.pi_service.verify_payment('invalid_payment')
        
        self.assertIsNone(result)
    
    @patch.dict(os.environ, {
        'PI_API_KEY': 'test-api-key',
        'PI_WALLET_PRIVATE_SEED': 'test-seed',
    }, clear=False)
    @patch('app.paypibridge.services.pi_service.PiNetwork')
    def test_create_app_to_user_payment_success(self, mock_pi_network_class):
        """Test create_app_to_user_payment returns payment ID when successful."""
        mock_client = MagicMock()
        mock_client.create_payment.return_value = 'payment_abc123'
        mock_pi_network_class.return_value = mock_client
        self.pi_service._pi_client = mock_client
        
        result = self.pi_service.create_app_to_user_payment(
            user_uid='user_123',
            amount=Decimal('10.5'),
            memo='Test payment',
            metadata={'order_id': '123'}
        )
        
        self.assertEqual(result, 'payment_abc123')
        mock_client.create_payment.assert_called_once()
        call_args = mock_client.create_payment.call_args[0][0]
        self.assertEqual(call_args['amount'], 10.5)
        self.assertEqual(call_args['uid'], 'user_123')
        self.assertEqual(call_args['memo'], 'Test payment')
    
    @patch.dict(os.environ, {
        'PI_API_KEY': 'test-api-key',
        'PI_WALLET_PRIVATE_SEED': 'test-seed',
    }, clear=False)
    @patch('app.paypibridge.services.pi_service.PiNetwork')
    def test_submit_payment_success(self, mock_pi_network_class):
        """Test submit_payment returns txid when successful."""
        mock_client = MagicMock()
        mock_client.submit_payment.return_value = 'txid_xyz789'
        mock_pi_network_class.return_value = mock_client
        self.pi_service._pi_client = mock_client
        
        result = self.pi_service.submit_payment('payment_123')
        
        self.assertEqual(result, 'txid_xyz789')
        mock_client.submit_payment.assert_called_once_with('payment_123', False)
    
    @patch.dict(os.environ, {
        'PI_API_KEY': 'test-api-key',
        'PI_WALLET_PRIVATE_SEED': 'test-seed',
    }, clear=False)
    @patch('app.paypibridge.services.pi_service.PiNetwork')
    def test_complete_payment_success(self, mock_pi_network_class):
        """Test complete_payment returns payment data when successful."""
        mock_client = MagicMock()
        mock_payment = {
            'id': 'payment_123',
            'status': 'completed',
            'txid': 'txid_xyz789'
        }
        mock_client.complete_payment.return_value = mock_payment
        mock_pi_network_class.return_value = mock_client
        self.pi_service._pi_client = mock_client
        
        result = self.pi_service.complete_payment('payment_123', 'txid_xyz789')
        
        self.assertEqual(result, mock_payment)
        mock_client.complete_payment.assert_called_once_with('payment_123', 'txid_xyz789')
    
    @patch.dict(os.environ, {
        'PI_API_KEY': 'test-api-key',
        'PI_WALLET_PRIVATE_SEED': 'test-seed',
    }, clear=False)
    @patch('app.paypibridge.services.pi_service.PiNetwork')
    def test_cancel_payment_success(self, mock_pi_network_class):
        """Test cancel_payment returns payment data when successful."""
        mock_client = MagicMock()
        mock_payment = {
            'id': 'payment_123',
            'status': 'cancelled'
        }
        mock_client.cancel_payment.return_value = mock_payment
        mock_pi_network_class.return_value = mock_client
        self.pi_service._pi_client = mock_client
        
        result = self.pi_service.cancel_payment('payment_123')
        
        self.assertEqual(result, mock_payment)
        mock_client.cancel_payment.assert_called_once_with('payment_123')
    
    @patch.dict(os.environ, {
        'PI_API_KEY': 'test-api-key',
        'PI_WALLET_PRIVATE_SEED': 'test-seed',
    }, clear=False)
    @patch('app.paypibridge.services.pi_service.PiNetwork')
    def test_get_incomplete_payments_success(self, mock_pi_network_class):
        """Test get_incomplete_payments returns list of payments."""
        mock_client = MagicMock()
        mock_payments = [
            {'id': 'payment_1', 'status': 'incomplete'},
            {'id': 'payment_2', 'status': 'incomplete'}
        ]
        mock_client.get_incomplete_server_payments.return_value = mock_payments
        mock_pi_network_class.return_value = mock_client
        self.pi_service._pi_client = mock_client
        
        result = self.pi_service.get_incomplete_payments()
        
        self.assertEqual(result, mock_payments)
        mock_client.get_incomplete_server_payments.assert_called_once()
    
    def test_get_pi_service_singleton(self):
        """Test get_pi_service returns singleton instance."""
        service1 = get_pi_service()
        service2 = get_pi_service()
        
        self.assertIs(service1, service2)
