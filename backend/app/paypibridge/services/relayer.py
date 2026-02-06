"""
Relayer Service for monitoring Soroban contract events.

This service monitors blockchain events from Soroban contracts
and triggers webhooks to the Django backend.
"""

import os
import logging
import hmac
import hashlib
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class SorobanRelayer:
    """
    Service for monitoring Soroban contract events and relaying them
    to the Django backend via webhooks.
    """
    
    def __init__(self):
        self.webhook_url = os.getenv('RELAYER_WEBHOOK_URL', 'http://localhost:8000/api/webhooks/ccip')
        self.webhook_secret = os.getenv('CCIP_WEBHOOK_SECRET', '')
        self.soroban_rpc_url = os.getenv('SOROBAN_RPC_URL', 'https://soroban-testnet.stellar.org')
        self.contract_id = os.getenv('SOROBAN_CONTRACT_ID', '')
        self.poll_interval = int(os.getenv('RELAYER_POLL_INTERVAL', '30'))  # seconds
        self.fx_service = None  # Will be imported to avoid circular dependency
    
    def process_intent_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Process an IntentCreated event from Soroban.
        
        Args:
            event_data: Event data from Soroban contract
            
        Returns:
            True if webhook was sent successfully, False otherwise
        """
        try:
            intent_id = event_data.get('intent_id')
            if not intent_id:
                logger.error("Intent event missing intent_id", extra={'event_data': event_data})
                return False
            
            # Get FX quote
            amount_pi = Decimal(str(event_data.get('amount_pi', '0')))
            fx_quote = self._get_fx_quote(amount_pi)
            
            # Prepare webhook payload
            payload = {
                'intent_id': intent_id,
                'event_id': f"evt_{intent_id}_{int(datetime.utcnow().timestamp())}",
                'event_type': event_data.get('event_type', 'IntentCreated'),
                'fx_quote': fx_quote,
                'status': event_data.get('status', 'CONFIRMED'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send webhook
            return self._send_webhook(payload)
            
        except Exception as e:
            logger.error(
                f"Error processing intent event: {e}",
                exc_info=True,
                extra={'event_data': event_data}
            )
            return False
    
    def _get_fx_quote(self, amount_pi: Decimal) -> Dict[str, Any]:
        """Get FX quote for amount in Pi."""
        try:
            # Import here to avoid circular dependency
            from .fx_service import get_fx_service
            fx_service = get_fx_service()
            return fx_service.get_quote(amount_pi)
        except Exception as e:
            logger.error(f"Error getting FX quote: {e}", exc_info=True)
            # Return fallback quote
            return {
                'amount_pi': str(amount_pi),
                'rate': '4.76',
                'amount_brl': str(amount_pi * Decimal('4.76')),
                'provider': 'fallback'
            }
    
    def _send_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        Send webhook to Django backend with HMAC signature.
        
        Args:
            payload: Webhook payload data
            
        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_secret:
            logger.error("CCIP_WEBHOOK_SECRET not configured")
            return False
        
        try:
            import json
            body = json.dumps(payload, separators=(',', ':')).encode('utf-8')
            
            # Generate HMAC signature
            signature = hmac.new(
                self.webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            # Send webhook
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'X-Signature': signature
                },
                timeout=10
            )
            
            response.raise_for_status()
            
            logger.info(
                f"Webhook sent successfully",
                extra={
                    'intent_id': payload.get('intent_id'),
                    'status_code': response.status_code
                }
            )
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error sending webhook: {e}",
                exc_info=True,
                extra={
                    'webhook_url': self.webhook_url,
                    'intent_id': payload.get('intent_id')
                }
            )
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error sending webhook: {e}",
                exc_info=True
            )
            return False
    
    def monitor_contract_events(self, last_ledger: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Monitor Soroban contract for new events.
        
        Args:
            last_ledger: Last processed ledger number (for pagination)
            
        Returns:
            List of new events
        """
        # This is a placeholder implementation
        # In production, this would:
        # 1. Connect to Soroban RPC
        # 2. Query contract events
        # 3. Filter for IntentCreated, DeliveryConfirmed, etc.
        # 4. Process each event
        
        logger.info(
            f"Monitoring Soroban contract events",
            extra={
                'contract_id': self.contract_id,
                'rpc_url': self.soroban_rpc_url,
                'last_ledger': last_ledger
            }
        )
        
        # Placeholder: return empty list
        # Real implementation would query Soroban RPC
        return []
    
    def process_event(self, event: Dict[str, Any]) -> bool:
        """
        Process a single Soroban event.
        
        Args:
            event: Event data from Soroban
            
        Returns:
            True if processed successfully
        """
        event_type = event.get('type')
        
        if event_type == 'IntentCreated':
            return self.process_intent_event(event)
        elif event_type == 'DeliveryConfirmed':
            return self._process_delivery_confirmed(event)
        elif event_type == 'IntentCancelled':
            return self._process_intent_cancelled(event)
        else:
            logger.warning(f"Unknown event type: {event_type}", extra={'event': event})
            return False
    
    def _process_delivery_confirmed(self, event_data: Dict[str, Any]) -> bool:
        """Process DeliveryConfirmed event."""
        try:
            intent_id = event_data.get('intent_id')
            payload = {
                'intent_id': intent_id,
                'event_id': f"evt_delivery_{intent_id}_{int(datetime.utcnow().timestamp())}",
                'event_type': 'DeliveryConfirmed',
                'status': 'SETTLED',
                'timestamp': datetime.utcnow().isoformat()
            }
            return self._send_webhook(payload)
        except Exception as e:
            logger.error(f"Error processing delivery confirmed: {e}", exc_info=True)
            return False
    
    def _process_intent_cancelled(self, event_data: Dict[str, Any]) -> bool:
        """Process IntentCancelled event."""
        try:
            intent_id = event_data.get('intent_id')
            payload = {
                'intent_id': intent_id,
                'event_id': f"evt_cancel_{intent_id}_{int(datetime.utcnow().timestamp())}",
                'event_type': 'IntentCancelled',
                'status': 'CANCELLED',
                'timestamp': datetime.utcnow().isoformat()
            }
            return self._send_webhook(payload)
        except Exception as e:
            logger.error(f"Error processing intent cancelled: {e}", exc_info=True)
            return False


# Singleton instance
_relayer_instance: Optional[SorobanRelayer] = None


def get_relayer() -> SorobanRelayer:
    """Get singleton instance of SorobanRelayer."""
    global _relayer_instance
    if _relayer_instance is None:
        _relayer_instance = SorobanRelayer()
    return _relayer_instance
