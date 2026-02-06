"""
Celery tasks for asynchronous processing.

Tasks for:
- Processing webhooks
- Monitoring Soroban events
- Processing payments
- Sending notifications
"""

import logging
from celery import shared_task
from django.utils import timezone
from decimal import Decimal

from .models import PaymentIntent, PixTransaction, WebhookEvent
from .services.pi_service import get_pi_service
from .services.fx_service import get_fx_service
from .services.relayer import get_relayer
from .clients.pix import PixClient

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_webhook_event(self, event_data: dict):
    """
    Process a webhook event asynchronously.
    
    Args:
        event_data: Webhook event data
        
    Returns:
        Processing result
    """
    try:
        intent_id = event_data.get('intent_id')
        event_id = event_data.get('event_id')
        
        # Check if already processed (idempotency)
        if event_id and WebhookEvent.objects.filter(event_id=event_id).exists():
            logger.info(
                f"Webhook event already processed",
                extra={'event_id': event_id, 'intent_id': intent_id}
            )
            return {'status': 'already_processed', 'event_id': event_id}
        
        # Get or create PaymentIntent
        try:
            intent = PaymentIntent.objects.get(intent_id=intent_id)
        except PaymentIntent.DoesNotExist:
            logger.error(
                f"PaymentIntent not found for webhook",
                extra={'intent_id': intent_id, 'event_id': event_id}
            )
            raise
        
        # Update intent with webhook data
        fx_quote = event_data.get('fx_quote', {})
        if fx_quote:
            intent.fx_quote = fx_quote
            if 'amount_brl' in fx_quote:
                intent.amount_brl = Decimal(str(fx_quote['amount_brl']))
        
        status = event_data.get('status')
        if status and status in dict(PaymentIntent.STATUS):
            intent.status = status
        
        intent.save()
        
        # Record webhook event
        if event_id:
            WebhookEvent.objects.get_or_create(
                intent_id=intent_id,
                event_id=event_id
            )
        
        logger.info(
            f"Webhook event processed successfully",
            extra={'event_id': event_id, 'intent_id': intent_id, 'status': status}
        )
        
        return {
            'status': 'success',
            'event_id': event_id,
            'intent_id': intent_id,
            'updated_status': status
        }
        
    except Exception as exc:
        logger.error(
            f"Error processing webhook event: {exc}",
            exc_info=True,
            extra={'event_data': event_data}
        )
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=3)
def monitor_soroban_events(self, last_ledger: int = None):
    """
    Monitor Soroban contract for new events.
    
    Args:
        last_ledger: Last processed ledger number
        
    Returns:
        Number of events processed
    """
    try:
        relayer = get_relayer()
        events = relayer.monitor_contract_events(last_ledger)
        
        processed = 0
        for event in events:
            if relayer.process_event(event):
                processed += 1
        
        logger.info(
            f"Soroban events monitored",
            extra={'events_found': len(events), 'processed': processed}
        )
        
        return {'events_found': len(events), 'processed': processed}
        
    except Exception as exc:
        logger.error(
            f"Error monitoring Soroban events: {exc}",
            exc_info=True
        )
        raise self.retry(exc=exc, countdown=60)  # Retry every minute


@shared_task(bind=True, max_retries=5)
def process_pix_payout(self, intent_id: str, consent_id: int):
    """
    Process Pix payout for a confirmed PaymentIntent.
    
    Args:
        intent_id: PaymentIntent ID
        consent_id: Consent ID for Open Finance
        
    Returns:
        Payout result
    """
    try:
        intent = PaymentIntent.objects.get(intent_id=intent_id)
        
        if intent.status != 'CONFIRMED':
            logger.warning(
                f"Intent not confirmed, skipping payout",
                extra={'intent_id': intent_id, 'status': intent.status}
            )
            return {'status': 'skipped', 'reason': 'not_confirmed'}
        
        # Get consent
        from .models import Consent
        try:
            consent = Consent.objects.get(id=consent_id, status='ACTIVE')
        except Consent.DoesNotExist:
            logger.error(
                f"Active consent not found",
                extra={'intent_id': intent_id, 'consent_id': consent_id}
            )
            raise
        
        # Create Pix payout
        pix_client = PixClient.from_env(consent=consent)
        
        # Get payout details from intent metadata or user
        payout_data = intent.metadata.get('payout', {})
        
        tx = pix_client.create_immediate_payment(
            cpf=payout_data.get('cpf', ''),
            pix_key=payout_data.get('pix_key', ''),
            amount_brl=str(intent.amount_brl or 0),
            description=f"Payment for intent {intent_id}"
        )
        
        # Create PixTransaction record
        pix_tx = PixTransaction.objects.create(
            intent=intent,
            tx_id=tx['txid'],
            status=tx['status'],
            payload=tx
        )
        
        # Update intent status
        intent.status = 'SETTLED'
        intent.save()
        
        logger.info(
            f"Pix payout processed successfully",
            extra={
                'intent_id': intent_id,
                'pix_tx_id': pix_tx.tx_id,
                'amount_brl': str(intent.amount_brl)
            }
        )
        
        return {
            'status': 'success',
            'pix_tx_id': pix_tx.tx_id,
            'intent_id': intent_id
        }
        
    except Exception as exc:
        logger.error(
            f"Error processing Pix payout: {exc}",
            exc_info=True,
            extra={'intent_id': intent_id, 'consent_id': consent_id}
        )
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task
def process_incomplete_payments():
    """
    Process incomplete Pi Network payments.
    Runs periodically to check for incomplete payments.
    """
    try:
        pi_service = get_pi_service()
        if not pi_service.is_available():
            logger.warning("Pi Network not available, skipping incomplete payments check")
            return {'status': 'skipped', 'reason': 'pi_unavailable'}
        
        incomplete = pi_service.get_incomplete_payments()
        
        processed = 0
        for payment in incomplete:
            payment_id = payment.get('id')
            if payment_id:
                # Process incomplete payment
                # This would typically submit it to blockchain
                logger.info(
                    f"Found incomplete payment",
                    extra={'payment_id': payment_id}
                )
                processed += 1
        
        logger.info(
            f"Incomplete payments processed",
            extra={'found': len(incomplete), 'processed': processed}
        )
        
        return {'found': len(incomplete), 'processed': processed}
        
    except Exception as e:
        logger.error(f"Error processing incomplete payments: {e}", exc_info=True)
        return {'status': 'error', 'error': str(e)}


@shared_task
def update_fx_rates():
    """
    Update FX rates cache.
    Runs periodically to refresh exchange rates.
    """
    try:
        fx_service = get_fx_service()
        rate = fx_service.get_rate()
        
        logger.info(
            f"FX rates updated",
            extra={'rate': str(rate), 'provider': fx_service.provider}
        )
        
        return {'rate': str(rate), 'provider': fx_service.provider}
        
    except Exception as e:
        logger.error(f"Error updating FX rates: {e}", exc_info=True)
        return {'status': 'error', 'error': str(e)}
