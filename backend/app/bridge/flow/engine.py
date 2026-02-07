"""
Engine de fluxo com state machine para PPBridge.
"""
import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from django.utils import timezone

from ..models import BridgeFlow, FlowEvent
from ..domain.enums import FlowStatus, EventType, can_transition
from ..adapters import get_adapter, AdapterError

logger = logging.getLogger(__name__)


class FlowEngine:
    """Engine que gerencia o fluxo de bridge com state machine."""
    
    def __init__(self, flow: BridgeFlow):
        self.flow = flow
    
    def transition_to(self, new_status: FlowStatus, metadata: Optional[Dict[str, Any]] = None) -> FlowEvent:
        """
        Transiciona o fluxo para um novo estado, registrando evento.
        
        Args:
            new_status: Novo estado
            metadata: Metadata adicional do evento
        
        Returns:
            FlowEvent criado
        
        Raises:
            ValueError: Se a transição não for válida
        """
        current_status = FlowStatus(self.flow.status)
        
        if not can_transition(current_status, new_status):
            raise ValueError(
                f"Invalid transition from {current_status.value} to {new_status.value}"
            )
        
        # Criar evento antes de atualizar estado
        event = FlowEvent.objects.create(
            flow=self.flow,
            event_type=EventType.STATE_CHANGE.value,
            from_state=current_status.value,
            to_state=new_status.value,
            metadata=metadata or {},
            correlation_id=self.flow.flow_id.hex,
        )
        
        # Atualizar estado
        self.flow.status = new_status.value
        if new_status == FlowStatus.COMPLETED:
            self.flow.completed_at = timezone.now()
        self.flow.save(update_fields=['status', 'completed_at', 'updated_at'])
        
        logger.info(
            f"Flow {self.flow.flow_id} transitioned: {current_status.value} -> {new_status.value}",
            extra={
                'flow_id': str(self.flow.flow_id),
                'from_state': current_status.value,
                'to_state': new_status.value,
            }
        )
        
        return event
    
    def log_event(
        self,
        event_type: EventType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FlowEvent:
        """
        Registra um evento sem mudança de estado.
        
        Args:
            event_type: Tipo do evento
            metadata: Metadata do evento
        
        Returns:
            FlowEvent criado
        """
        event = FlowEvent.objects.create(
            flow=self.flow,
            event_type=event_type.value,
            metadata=metadata or {},
            correlation_id=self.flow.flow_id.hex,
        )
        
        logger.info(
            f"Flow {self.flow.flow_id} event: {event_type.value}",
            extra={
                'flow_id': str(self.flow.flow_id),
                'event_type': event_type.value,
                'metadata': metadata,
            }
        )
        
        return event
    
    def execute_flow(self) -> None:
        """
        Executa o fluxo completo de bridge.
        
        Esta função processa o fluxo sincronamente, transicionando pelos estados
        e executando os adapters apropriados.
        """
        try:
            # 1. VALIDATED: Validar source e target
            self._validate_adapters()
            self.transition_to(FlowStatus.VALIDATED)
            
            # 2. BRIDGING: Preparar e executar transferências
            self.transition_to(FlowStatus.BRIDGING)
            self._execute_bridging()
            
            # 3. CONVERTED (opcional): Se houver conversão de moeda
            # Por enquanto, pulamos direto para COMPLETED
            
            # 4. COMPLETED: Finalizar
            self.transition_to(FlowStatus.COMPLETED)
            
        except AdapterError as e:
            logger.error(
                f"Adapter error in flow {self.flow.flow_id}: {e.code} - {e.message}",
                exc_info=True,
                extra={
                    'flow_id': str(self.flow.flow_id),
                    'error_code': e.code,
                    'error_message': e.message,
                    'error_details': e.details,
                }
            )
            self.flow.error_code = e.code
            self.flow.error_message = e.message
            self.flow.save(update_fields=['error_code', 'error_message'])
            self.transition_to(FlowStatus.FAILED, metadata={
                'error_code': e.code,
                'error_message': e.message,
                'error_details': e.details,
            })
            raise
        
        except Exception as e:
            logger.error(
                f"Unexpected error in flow {self.flow.flow_id}: {str(e)}",
                exc_info=True,
                extra={'flow_id': str(self.flow.flow_id)}
            )
            self.flow.error_code = "INTERNAL_ERROR"
            self.flow.error_message = str(e)
            self.flow.save(update_fields=['error_code', 'error_message'])
            self.transition_to(FlowStatus.FAILED, metadata={
                'error_code': 'INTERNAL_ERROR',
                'error_message': str(e),
            })
            raise
    
    def _validate_adapters(self) -> None:
        """Valida source e target usando os adapters."""
        # Validar source (crypto)
        source_adapter = get_adapter(self.flow.source_domain, self.flow.source_adapter)
        source_metadata = {**self.flow.source_metadata, 'flow_id': str(self.flow.flow_id)}
        
        source_validation = source_adapter.validate_source(self.flow.amount, source_metadata)
        self.log_event(EventType.ADAPTER_VALIDATION, metadata={
            'adapter': f"{self.flow.source_domain}/{self.flow.source_adapter}",
            'validation_result': source_validation,
        })
        
        # Validar target (finance)
        target_adapter = get_adapter(self.flow.target_domain, self.flow.target_adapter)
        target_metadata = {**self.flow.target_metadata, 'flow_id': str(self.flow.flow_id)}
        
        target_validation = target_adapter.validate_target(self.flow.amount, target_metadata)
        self.log_event(EventType.ADAPTER_VALIDATION, metadata={
            'adapter': f"{self.flow.target_domain}/{self.flow.target_adapter}",
            'validation_result': target_validation,
        })
    
    def _execute_bridging(self) -> None:
        """Executa o bridging: lock, transfer, confirm."""
        # 1. Lock/prepare source
        source_adapter = get_adapter(self.flow.source_domain, self.flow.source_adapter)
        source_metadata = {**self.flow.source_metadata, 'flow_id': str(self.flow.flow_id)}
        
        source_lock = source_adapter.lock_or_prepare(
            str(self.flow.flow_id),
            self.flow.amount,
            source_metadata
        )
        self.log_event(EventType.ADAPTER_EXECUTION, metadata={
            'adapter': f"{self.flow.source_domain}/{self.flow.source_adapter}",
            'action': 'lock',
            'result': source_lock,
        })
        
        # 2. Lock/prepare target
        target_adapter = get_adapter(self.flow.target_domain, self.flow.target_adapter)
        target_metadata = {**self.flow.target_metadata, 'flow_id': str(self.flow.flow_id)}
        
        target_prepare = target_adapter.lock_or_prepare(
            str(self.flow.flow_id),
            self.flow.amount,
            target_metadata
        )
        self.log_event(EventType.ADAPTER_EXECUTION, metadata={
            'adapter': f"{self.flow.target_domain}/{self.flow.target_adapter}",
            'action': 'prepare',
            'result': target_prepare,
        })
        
        # 3. Execute source transfer
        source_transfer = source_adapter.execute_transfer(
            str(self.flow.flow_id),
            self.flow.amount,
            source_metadata
        )
        self.log_event(EventType.ADAPTER_EXECUTION, metadata={
            'adapter': f"{self.flow.source_domain}/{self.flow.source_adapter}",
            'action': 'transfer',
            'result': source_transfer,
        })
        
        # 4. Confirm source
        source_confirm = source_adapter.confirm(str(self.flow.flow_id), source_transfer)
        self.log_event(EventType.ADAPTER_EXECUTION, metadata={
            'adapter': f"{self.flow.source_domain}/{self.flow.source_adapter}",
            'action': 'confirm',
            'result': source_confirm,
        })
        
        # 5. Execute target transfer
        target_transfer = target_adapter.execute_transfer(
            str(self.flow.flow_id),
            self.flow.amount,
            target_metadata
        )
        self.log_event(EventType.ADAPTER_EXECUTION, metadata={
            'adapter': f"{self.flow.target_domain}/{self.flow.target_adapter}",
            'action': 'transfer',
            'result': target_transfer,
        })
        
        # 6. Confirm target
        target_confirm = target_adapter.confirm(str(self.flow.flow_id), target_transfer)
        self.log_event(EventType.ADAPTER_EXECUTION, metadata={
            'adapter': f"{self.flow.target_domain}/{self.flow.target_adapter}",
            'action': 'confirm',
            'result': target_confirm,
        })
        
        # 7. Salvar resultado
        self.flow.result = {
            'source_transfer': source_transfer,
            'target_transfer': target_transfer,
            'target_reference': target_transfer.get('pix_tx_id') or target_transfer.get('reference_id'),
        }
        self.flow.save(update_fields=['result'])
    
    def cancel(self, reason: Optional[str] = None) -> None:
        """
        Cancela o fluxo.
        
        Args:
            reason: Motivo do cancelamento
        """
        if not self.flow.can_cancel():
            raise ValueError(f"Cannot cancel flow in status {self.flow.status}")
        
        self.transition_to(FlowStatus.CANCELED, metadata={
            'reason': reason or 'User requested cancellation',
        })
