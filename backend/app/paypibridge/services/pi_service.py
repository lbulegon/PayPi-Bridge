"""
Pi Network Integration Service

This service integrates with Pi Network using the pi-python SDK.
Handles authentication, payment validation, and transaction tracking.
"""

import os
import sys
from typing import Optional, Dict, Any
from decimal import Decimal

# SDK Pi Network: PayPi-Bridge/backend/pi_sdk/ (único uso)
_backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
_pi_sdk_path = os.path.abspath(os.path.join(_backend_root, "pi_sdk"))
if os.path.exists(_pi_sdk_path) and _pi_sdk_path not in sys.path:
    sys.path.insert(0, _pi_sdk_path)

try:
    from pi_python import PiNetwork
except ImportError:
    PiNetwork = None


class PiService:
    """
    Service for interacting with Pi Network API.
    """
    
    def __init__(self):
        self.api_key = os.getenv('PI_API_KEY', '')
        self.wallet_private_seed = os.getenv('PI_WALLET_PRIVATE_SEED', '')
        self.network = os.getenv('PI_NETWORK', 'Pi Testnet')
        self._pi_client: Optional[PiNetwork] = None
        
    def _get_client(self) -> Optional[PiNetwork]:
        """Get or initialize Pi Network client."""
        if PiNetwork is None:
            return None
            
        if self._pi_client is None:
            if not self.api_key or not self.wallet_private_seed:
                return None
                
            try:
                self._pi_client = PiNetwork()
                self._pi_client.initialize(
                    self.api_key,
                    self.wallet_private_seed,
                    self.network
                )
            except Exception as e:
                print(f"Error initializing Pi Network client: {e}")
                return None
                
        return self._pi_client
    
    def is_available(self) -> bool:
        """Check if Pi Network integration is available."""
        return self._get_client() is not None
    
    def get_balance(self) -> Optional[Decimal]:
        """
        Get the current Pi balance of the app wallet.
        
        Returns:
            Decimal balance or None if unavailable
        """
        client = self._get_client()
        if not client:
            return None
            
        try:
            balance = client.get_balance()
            return Decimal(str(balance)) if balance is not None else None
        except Exception as e:
            print(f"Error getting Pi balance: {e}")
            return None
    
    def verify_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Verify a payment by its ID.
        
        Args:
            payment_id: Payment identifier from Pi Network
            
        Returns:
            Payment data dict or None if not found/invalid
        """
        client = self._get_client()
        if not client:
            return None
            
        try:
            payment = client.get_payment(payment_id)
            if payment and 'error' not in payment:
                return payment
            return None
        except Exception as e:
            print(f"Error verifying payment {payment_id}: {e}")
            return None
    
    def create_app_to_user_payment(
        self,
        user_uid: str,
        amount: Decimal,
        memo: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Create an App-to-User payment (payout).
        
        Args:
            user_uid: Unique user identifier from Pi Network
            amount: Amount in Pi
            memo: Payment description
            metadata: Additional metadata
            
        Returns:
            Payment ID or None if creation failed
        """
        client = self._get_client()
        if not client:
            return None
            
        try:
            payment_data = {
                "amount": float(amount),
                "memo": memo,
                "metadata": metadata or {},
                "uid": user_uid
            }
            
            payment_id = client.create_payment(payment_data)
            return payment_id if payment_id else None
        except Exception as e:
            print(f"Error creating A2U payment: {e}")
            return None
    
    def submit_payment(self, payment_id: str) -> Optional[str]:
        """
        Submit a payment to the Pi blockchain.
        
        Args:
            payment_id: Payment identifier
            
        Returns:
            Transaction ID (txid) or None if submission failed
        """
        client = self._get_client()
        if not client:
            return None
            
        try:
            txid = client.submit_payment(payment_id, False)
            return txid if txid else None
        except Exception as e:
            print(f"Error submitting payment {payment_id}: {e}")
            return None
    
    def complete_payment(self, payment_id: str, txid: str) -> Optional[Dict[str, Any]]:
        """
        Complete a payment after blockchain confirmation.
        
        Args:
            payment_id: Payment identifier
            txid: Transaction ID from blockchain
            
        Returns:
            Completed payment data or None if completion failed
        """
        client = self._get_client()
        if not client:
            return None
            
        try:
            payment = client.complete_payment(payment_id, txid)
            return payment if payment and 'error' not in payment else None
        except Exception as e:
            print(f"Error completing payment {payment_id}: {e}")
            return None
    
    def cancel_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Cancel a payment.
        
        Args:
            payment_id: Payment identifier
            
        Returns:
            Cancelled payment data or None if cancellation failed
        """
        client = self._get_client()
        if not client:
            return None
            
        try:
            payment = client.cancel_payment(payment_id)
            return payment if payment and 'error' not in payment else None
        except Exception as e:
            print(f"Error cancelling payment {payment_id}: {e}")
            return None
    
    def get_incomplete_payments(self) -> list:
        """
        Get list of incomplete payments that need to be processed.
        
        Returns:
            List of incomplete payment objects
        """
        client = self._get_client()
        if not client:
            return []
            
        try:
            payments = client.get_incomplete_server_payments()
            return payments if payments else []
        except Exception as e:
            print(f"Error getting incomplete payments: {e}")
            return []


# Singleton instance
_pi_service_instance: Optional[PiService] = None


def get_pi_service() -> PiService:
    """Get singleton instance of PiService."""
    global _pi_service_instance
    if _pi_service_instance is None:
        _pi_service_instance = PiService()
    return _pi_service_instance
