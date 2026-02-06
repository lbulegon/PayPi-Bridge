"""
Consent Management Service

Gerencia consentimentos Open Finance, incluindo criação, validação e renovação.
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from app.paypibridge.models import Consent, BankAccount
from app.paypibridge.clients.open_finance import OpenFinanceClient

User = get_user_model()


class ConsentService:
    """
    Serviço para gerenciamento de consentimentos Open Finance.
    """
    
    def __init__(self, of_client: Optional[OpenFinanceClient] = None):
        self.of_client = of_client or OpenFinanceClient.from_env()
    
    def create_consent(
        self,
        user: User,
        provider: str,
        scopes: List[str],
        expiration_days: int = 90
    ) -> Optional[Consent]:
        """
        Cria um novo consentimento Open Finance.
        
        Args:
            user: Usuário Django
            provider: Nome do provedor/banco
            scopes: Lista de escopos (ex: ["payments", "accounts"])
            expiration_days: Dias até expiração (padrão: 90)
            
        Returns:
            Consent criado ou None se falhar
        """
        # Criar consentimento via Open Finance API
        expiration_date = datetime.now() + timedelta(days=expiration_days)
        
        consent_data = self.of_client.create_consent(
            user_id=str(user.id),  # Usar ID do usuário como identificador
            scopes=scopes,
            expiration_date=expiration_date
        )
        
        if not consent_data:
            return None
        
        # Extrair consent_id da resposta
        consent_id = consent_data.get("data", {}).get("consentId")
        if not consent_id:
            # Tentar outros formatos possíveis
            consent_id = consent_data.get("consentId") or consent_data.get("id")
        
        if not consent_id:
            print("Warning: Could not extract consent_id from response")
            return None
        
        # Salvar no banco de dados
        consent = Consent.objects.create(
            user=user,
            provider=provider,
            scope={"scopes": scopes},
            consent_id=consent_id,
            status="ACTIVE",
            expires_at=expiration_date
        )
        
        return consent
    
    def refresh_consent(self, consent: Consent) -> bool:
        """
        Atualiza dados de um consentimento existente.
        
        Args:
            consent: Consentimento a atualizar
            
        Returns:
            True se atualizado com sucesso
        """
        consent_data = self.of_client.get_consent(consent.consent_id)
        
        if not consent_data:
            return False
        
        # Atualizar status
        status = consent_data.get("data", {}).get("status", "UNKNOWN")
        consent.status = status.upper()
        
        # Atualizar data de expiração se disponível
        expiration_str = consent_data.get("data", {}).get("expirationDateTime")
        if expiration_str:
            try:
                consent.expires_at = datetime.fromisoformat(expiration_str.replace('Z', '+00:00'))
            except:
                pass
        
        consent.save()
        return True
    
    def validate_consent(self, consent: Consent) -> bool:
        """
        Valida se um consentimento está ativo e válido.
        
        Args:
            consent: Consentimento a validar
            
        Returns:
            True se válido, False caso contrário
        """
        # Verificar se está expirado
        if consent.expires_at and timezone.now() > consent.expires_at:
            consent.status = "EXPIRED"
            consent.save()
            return False
        
        # Verificar status
        if consent.status != "ACTIVE":
            return False
        
        # Atualizar dados do servidor
        self.refresh_consent(consent)
        
        # Verificar novamente após refresh
        return consent.status == "ACTIVE"
    
    def get_active_consent(
        self,
        user: User,
        provider: Optional[str] = None
    ) -> Optional[Consent]:
        """
        Obtém consentimento ativo de um usuário.
        
        Args:
            user: Usuário Django
            provider: Nome do provedor (opcional, filtra por provedor)
            
        Returns:
            Consentimento ativo ou None se não encontrado
        """
        query = Consent.objects.filter(
            user=user,
            status="ACTIVE"
        )
        
        if provider:
            query = query.filter(provider=provider)
        
        consent = query.first()
        
        if consent:
            # Validar antes de retornar
            if self.validate_consent(consent):
                return consent
            else:
                return None
        
        return None
    
    def link_bank_account(
        self,
        consent: Consent,
        institution: str,
        account_id: str,
        branch: str = "",
        number: str = "",
        ispb: str = ""
    ) -> Optional[BankAccount]:
        """
        Vincula uma conta bancária a um consentimento.
        
        Args:
            consent: Consentimento
            institution: Nome da instituição
            account_id: ID da conta
            branch: Agência (opcional)
            number: Número da conta (opcional)
            ispb: ISPB da instituição (opcional)
            
        Returns:
            BankAccount criado ou None se falhar
        """
        # Obter contas do Open Finance
        accounts = self.of_client.get_accounts(consent.consent_id)
        
        if not accounts:
            # Criar sem validação se não conseguir obter
            return BankAccount.objects.create(
                user=consent.user,
                consent=consent,
                institution=institution,
                account_id=account_id,
                branch=branch,
                number=number,
                ispb=ispb
            )
        
        # Validar se conta existe na lista
        for account in accounts:
            if account.get("accountId") == account_id:
                # Conta encontrada, criar registro
                return BankAccount.objects.create(
                    user=consent.user,
                    consent=consent,
                    institution=institution,
                    account_id=account_id,
                    branch=branch,
                    number=number,
                    ispb=ispb
                )
        
        # Conta não encontrada, criar mesmo assim (pode ser válida mas não listada)
        return BankAccount.objects.create(
            user=consent.user,
            consent=consent,
            institution=institution,
            account_id=account_id,
            branch=branch,
            number=number,
            ispb=ispb
        )


# Singleton instance
_consent_service_instance: Optional[ConsentService] = None


def get_consent_service() -> ConsentService:
    """Get singleton instance of ConsentService."""
    global _consent_service_instance
    if _consent_service_instance is None:
        _consent_service_instance = ConsentService()
    return _consent_service_instance
