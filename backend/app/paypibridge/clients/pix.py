"""
Pix Client - Wrapper para Open Finance Payments Initiation API

Simplifica a criação de pagamentos Pix usando o OpenFinanceClient.
"""

from typing import Optional, Dict, Any
from .open_finance import OpenFinanceClient
from app.paypibridge.models import Consent


class PixClient:
    """
    Cliente simplificado para criação de pagamentos Pix.
    
    Wrapper sobre OpenFinanceClient que facilita o uso
    com consentimentos já armazenados no banco.
    """
    
    def __init__(self, of: OpenFinanceClient, consent: Optional[Consent] = None):
        self.of = of
        self.consent = consent
    
    @classmethod
    def from_env(cls, consent: Optional[Consent] = None):
        """Cria cliente a partir de variáveis de ambiente."""
        return cls(OpenFinanceClient.from_env(), consent)
    
    def create_immediate_payment(
        self,
        cpf: str,
        pix_key: str,
        amount_brl: str,
        description: str = "",
        end_to_end_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria um pagamento Pix imediato.
        
        Args:
            cpf: CPF do pagador
            pix_key: Chave Pix do beneficiário (CPF, email, telefone, chave aleatória)
            amount_brl: Valor em BRL (string, ex: "100.00")
            description: Descrição do pagamento
            end_to_end_id: ID end-to-end (opcional)
            
        Returns:
            Dados da transação Pix criada
            
        Raises:
            ValueError: Se consentimento não estiver disponível
        """
        if not self.consent:
            raise ValueError("Consent is required to create Pix payment")
        
        if self.consent.status != "ACTIVE":
            raise ValueError(f"Consent status is {self.consent.status}, must be ACTIVE")
        
        # Validar formato do valor
        try:
            float(amount_brl)
        except ValueError:
            raise ValueError(f"Invalid amount format: {amount_brl}")
        
        # Criar pagamento via Open Finance
        result = self.of.create_pix_payment(
            consent_id=self.consent.consent_id,
            cpf=cpf,
            pix_key=pix_key,
            amount_brl=amount_brl,
            description=description,
            end_to_end_id=end_to_end_id
        )
        
        return result
    
    def get_payment_status(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém status de um pagamento Pix.
        
        Args:
            payment_id: ID do pagamento (E2E ID)
            
        Returns:
            Status do pagamento ou None se falhar
        """
        if not self.consent:
            return None
        
        return self.of.get_payment_status(
            consent_id=self.consent.consent_id,
            payment_id=payment_id
        )
    
    def reconcile_payment(
        self,
        account_id: str,
        expected_amount: str,
        expected_txid: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Reconcilia um pagamento verificando transações da conta.
        
        Args:
            account_id: ID da conta bancária
            expected_amount: Valor esperado
            expected_txid: ID da transação esperado (opcional)
            
        Returns:
            Dados da reconciliação ou None se não encontrado
        """
        if not self.consent:
            return None
        
        return self.of.reconcile_payment(
            consent_id=self.consent.consent_id,
            account_id=account_id,
            expected_amount=expected_amount,
            expected_txid=expected_txid
        )
