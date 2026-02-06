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
        self._last_ledger: Optional[int] = None
        self._server: Optional[Any] = None  # Server type only if STELLAR_SDK_AVAILABLE
    
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
    
    def _get_server(self) -> Optional[Any]:
        """Get or create Stellar/Soroban server instance."""
        if not STELLAR_SDK_AVAILABLE:
            return None
        
        if self._server is None:
            try:
                from stellar_sdk import Server
                self._server = Server(self.soroban_rpc_url)
                logger.info(f"Soroban server initialized", extra={'rpc_url': self.soroban_rpc_url})
            except Exception as e:
                logger.error(f"Error initializing Soroban server: {e}", exc_info=True)
                return None
        
        return self._server
    
    def monitor_contract_events(self, last_ledger: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Monitor Soroban contract for new events.
        
        Args:
            last_ledger: Last processed ledger number (for pagination)
            
        Returns:
            List of new events
        """
        if not self.contract_id:
            logger.warning("SOROBAN_CONTRACT_ID not configured, skipping event monitoring")
            return []
        
        server = self._get_server()
        if not server:
            logger.warning("Soroban server not available, using fallback")
            return []
        
        try:
            # Get current ledger
            current_ledger = server.fetch_latest_ledger()
            start_ledger = last_ledger or (current_ledger - 100)  # Look back 100 ledgers if no last_ledger
            
            logger.info(
                f"Querying Soroban events",
                extra={
                    'contract_id': self.contract_id,
                    'start_ledger': start_ledger,
                    'current_ledger': current_ledger
                }
            )
            
            # Query events using Soroban RPC
            events = self._query_soroban_events(server, start_ledger, current_ledger)
            
            # Update last processed ledger
            if events:
                self._last_ledger = current_ledger
            
            logger.info(
                f"Soroban events queried",
                extra={
                    'events_found': len(events),
                    'last_ledger': self._last_ledger
                }
            )
            
            return events
            
        except Exception as e:
            logger.error(
                f"Error monitoring Soroban events: {e}",
                exc_info=True,
                extra={
                    'contract_id': self.contract_id,
                    'rpc_url': self.soroban_rpc_url
                }
            )
            return []
    
    def _query_soroban_events(
        self,
        server: Any,
        start_ledger: int,
        end_ledger: int
    ) -> List[Dict[str, Any]]:
        """
        Query Soroban contract events from RPC.
        
        Args:
            server: Stellar server instance
            start_ledger: Starting ledger number
            end_ledger: Ending ledger number
            
        Returns:
            List of parsed events
        """
        events = []
        
        try:
            # Use Soroban RPC getEvents endpoint via REST API
            # Note: Soroban RPC uses JSON-RPC, but we'll use REST for simplicity
            # Real implementation could use stellar-sdk's event streaming
            
            rpc_endpoint = f"{self.soroban_rpc_url.rstrip('/')}/events"
            
            payload = {
                "contractIds": [self.contract_id],
                "startLedger": start_ledger,
                "endLedger": end_ledger,
                "filters": [
                    {
                        "type": "contract",
                        "contractIds": [self.contract_id],
                        "topics": [
                            ["IntentCreated"],
                            ["DeliveryConfirmed"],
                            ["IntentCancelled"]
                        ]
                    }
                ]
            }
            
            response = requests.post(
                rpc_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                events_data = data.get("events", [])
                
                for event_data in events_data:
                    parsed_event = self._parse_soroban_event(event_data)
                    if parsed_event:
                        events.append(parsed_event)
            
            else:
                logger.warning(
                    f"Soroban RPC returned non-200 status",
                    extra={'status_code': response.status_code, 'response': response.text[:200]}
                )
                
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error querying Soroban RPC: {e}",
                exc_info=True,
                extra={'rpc_endpoint': rpc_endpoint}
            )
        except Exception as e:
            logger.error(
                f"Unexpected error querying Soroban events: {e}",
                exc_info=True
            )
        
        return events
    
    def _parse_soroban_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a Soroban event into our internal format.
        
        Args:
            event_data: Raw event data from Soroban RPC
            
        Returns:
            Parsed event dict or None if invalid
        """
        try:
            # Extract event type from topics
            topics = event_data.get("topics", [])
            if not topics:
                return None
            
            event_type = None
            if "IntentCreated" in str(topics):
                event_type = "IntentCreated"
            elif "DeliveryConfirmed" in str(topics):
                event_type = "DeliveryConfirmed"
            elif "IntentCancelled" in str(topics):
                event_type = "IntentCancelled"
            
            if not event_type:
                return None
            
            # Extract event data
            value = event_data.get("value", {})
            xdr_data = value.get("xdr", "")
            
            # Parse XDR data (simplified - real implementation would decode XDR)
            # For now, extract what we can from the event structure
            parsed = {
                "type": event_type,
                "ledger": event_data.get("ledger"),
                "timestamp": event_data.get("timestamp"),
                "contract_id": self.contract_id,
                "raw_event": event_data
            }
            
            # Try to extract intent_id and other fields from XDR or value
            # This is simplified - real implementation would decode XDR properly
            if event_type == "IntentCreated":
                # Extract from value if available
                parsed["intent_id"] = event_data.get("id") or f"intent_{event_data.get('ledger')}"
                parsed["amount_pi"] = event_data.get("amount_pi", "0")
            elif event_type in ["DeliveryConfirmed", "IntentCancelled"]:
                parsed["intent_id"] = event_data.get("intent_id") or event_data.get("id")
            
            return parsed
            
        except Exception as e:
            logger.error(
                f"Error parsing Soroban event: {e}",
                exc_info=True,
                extra={'event_data': event_data}
            )
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get relayer status and configuration.
        
        Returns:
            Status information
        """
        server = self._get_server()
        is_connected = server is not None
        
        return {
            "enabled": bool(self.contract_id and self.webhook_secret),
            "rpc_url": self.soroban_rpc_url,
            "contract_id": self.contract_id or "not_configured",
            "webhook_url": self.webhook_url,
            "poll_interval": self.poll_interval,
            "connected": is_connected,
            "last_ledger": self._last_ledger,
            "stellar_sdk_available": STELLAR_SDK_AVAILABLE
        }
    
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
