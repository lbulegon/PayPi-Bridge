"""
Tests for PayPiBridge models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from app.paypibridge.models import (
    PaymentIntent, Consent, BankAccount,
    PixTransaction, Escrow
)

User = get_user_model()


class PaymentIntentModelTest(TestCase):
    """Tests for PaymentIntent model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_payment_intent(self):
        """Test creating a PaymentIntent."""
        intent = PaymentIntent.objects.create(
            intent_id="pi_1234567890",
            payer_address="GABC123...",
            payee_user=self.user,
            amount_pi=Decimal("10.5"),
            status="CREATED"
        )
        
        self.assertEqual(intent.intent_id, "pi_1234567890")
        self.assertEqual(intent.amount_pi, Decimal("10.5"))
        self.assertEqual(intent.status, "CREATED")
        self.assertIsNotNone(intent.created_at)
    
    def test_payment_intent_str(self):
        """Test PaymentIntent string representation."""
        intent = PaymentIntent.objects.create(
            intent_id="pi_1234567890",
            payer_address="GABC123...",
            payee_user=self.user,
            amount_pi=Decimal("10.5")
        )
        
        self.assertIn("pi_1234567890", str(intent))
    
    def test_payment_intent_status_transitions(self):
        """Test PaymentIntent status transitions."""
        intent = PaymentIntent.objects.create(
            intent_id="pi_1234567890",
            payer_address="GABC123...",
            payee_user=self.user,
            amount_pi=Decimal("10.5"),
            status="CREATED"
        )
        
        # Transition to CONFIRMED
        intent.status = "CONFIRMED"
        intent.save()
        self.assertEqual(intent.status, "CONFIRMED")
        
        # Transition to SETTLED
        intent.status = "SETTLED"
        intent.save()
        self.assertEqual(intent.status, "SETTLED")


class ConsentModelTest(TestCase):
    """Tests for Consent model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_consent(self):
        """Test creating a Consent."""
        consent = Consent.objects.create(
            user=self.user,
            provider="bank_example",
            scope={"payments": "read", "accounts": "read"},
            consent_id="consent_123",
            status="ACTIVE"
        )
        
        self.assertEqual(consent.user, self.user)
        self.assertEqual(consent.provider, "bank_example")
        self.assertEqual(consent.consent_id, "consent_123")
        self.assertEqual(consent.status, "ACTIVE")
        self.assertIsNotNone(consent.created_at)


class PixTransactionModelTest(TestCase):
    """Tests for PixTransaction model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.intent = PaymentIntent.objects.create(
            intent_id="pi_1234567890",
            payer_address="GABC123...",
            payee_user=self.user,
            amount_pi=Decimal("10.5")
        )
    
    def test_create_pix_transaction(self):
        """Test creating a PixTransaction."""
        pix_tx = PixTransaction.objects.create(
            intent=self.intent,
            tx_id="E2E123456789",
            status="SENT",
            payload={"amount": "100.00", "cpf": "12345678901"}
        )
        
        self.assertEqual(pix_tx.intent, self.intent)
        self.assertEqual(pix_tx.tx_id, "E2E123456789")
        self.assertEqual(pix_tx.status, "SENT")
        self.assertIsNotNone(pix_tx.created_at)


class EscrowModelTest(TestCase):
    """Tests for Escrow model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.intent = PaymentIntent.objects.create(
            intent_id="pi_1234567890",
            payer_address="GABC123...",
            payee_user=self.user,
            amount_pi=Decimal("10.5")
        )
    
    def test_create_escrow(self):
        """Test creating an Escrow."""
        escrow = Escrow.objects.create(
            intent=self.intent,
            release_condition="DELIVERY_CONFIRMED",
            deadline=timezone.now()
        )
        
        self.assertEqual(escrow.intent, self.intent)
        self.assertEqual(escrow.release_condition, "DELIVERY_CONFIRMED")
        self.assertIsNotNone(escrow.deadline)
