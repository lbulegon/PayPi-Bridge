"""
Adapter stub para Pix (finance target).
"""
import logging
from decimal import Decimal
from typing import Dict, Any
from .base import FinanceAdapter, AdapterError

logger = logging.getLogger(__name__)


class PixStubAdapter(FinanceAdapter):
    """Adapter stub para Pix - implementação mock realista."""
    
    def validate_target(self, amount: Decimal, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Valida destino Pix."""
        logger.info(f"PixStub: Validating target for amount {amount}")
        
        pix_key = metadata.get("pix_key") or metadata.get("target_pix_key")
        if not pix_key:
            raise AdapterError(
                code="MISSING_PIX_KEY",
                message="Pix key is required",
                details={"metadata": metadata}
            )
        
        # Mock: valida formato básico
        if len(pix_key) < 10:
            raise AdapterError(
                code="INVALID_PIX_KEY",
                message="Pix key format is invalid",
                details={"pix_key": pix_key}
            )
        
        return {
            "valid": True,
            "pix_key": pix_key,
            "account_valid": True,
            "can_receive": True,
        }
    
    def lock_or_prepare(self, flow_id: str, amount: Decimal, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara destino Pix."""
        logger.info(f"PixStub: Preparing Pix destination for flow {flow_id}")
        
        return {
            "prepared": True,
            "destination_ready": True,
            "estimated_settlement_time": "instant",
        }
    
    def execute_transfer(self, flow_id: str, amount: Decimal, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Executa transferência Pix."""
        logger.info(f"PixStub: Executing Pix transfer of {amount} BRL for flow {flow_id}")
        
        pix_key = metadata.get("pix_key") or metadata.get("target_pix_key")
        
        # Mock: simula transferência Pix bem-sucedida
        return {
            "reference_id": f"PIX_{flow_id}",
            "pix_tx_id": f"pix_tx_{flow_id}",
            "end_to_end_id": f"E{flow_id.upper().replace('-', '')[:32]}",
            "status": "settled",
            "settled_at": "2026-02-07T00:00:00Z",
        }
    
    def confirm(self, flow_id: str, transfer_result: Dict[str, Any]) -> Dict[str, Any]:
        """Confirma transferência Pix."""
        logger.info(f"PixStub: Confirming Pix transfer for flow {flow_id}")
        
        return {
            "confirmed": True,
            "settlement_confirmed": True,
            "final": True,
        }
    
    def rollback_or_compensate(self, flow_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Reverte transferência Pix (best-effort)."""
        logger.warning(f"PixStub: Attempting rollback for flow {flow_id}")
        
        # Mock: Pix é irreversível, então retorna compensação
        return {
            "rolled_back": False,
            "compensation_required": True,
            "compensation_reference": f"PIX_COMP_{flow_id}",
            "status": "compensation_initiated",
        }
