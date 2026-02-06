"""
Open Finance Client - Implementação Real

Cliente para integração com Open Banking Brasil seguindo as especificações:
- mTLS (mutual TLS) para autenticação
- OAuth2 para autorização
- Consent Management
- Payments Initiation API (Pix)
- Accounts/Transactions API
"""

import os
import uuid
import requests
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import ssl
import certifi


def _of_use_mock() -> bool:
    """True se OF não configurado ou OF_USE_MOCK ativo (sandbox/mock para desenvolvimento)."""
    base = (os.getenv("OF_BASE_URL") or "").strip()
    mock = (os.getenv("OF_USE_MOCK") or "").lower() in ("1", "true", "yes")
    return not base or mock


class OpenFinanceClient:
    """
    Cliente para integração com Open Banking Brasil.
    
    Implementa:
    - mTLS (mutual TLS) com certificados cliente
    - OAuth2 flow para obtenção de tokens
    - Consent management
    - Payments Initiation API (Pix)
    - Accounts/Transactions API
    """
    
    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        mtls_cert_path: Optional[str] = None,
        mtls_key_path: Optional[str] = None,
        ca_cert_path: Optional[str] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.mtls_cert_path = mtls_cert_path
        self.mtls_key_path = mtls_key_path
        self.ca_cert_path = ca_cert_path
        self._is_mock = _of_use_mock()

        # Cache de tokens OAuth2
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

        # Configurar sessão HTTP com mTLS (só quando não for mock)
        self._session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Cria sessão HTTP com mTLS configurado."""
        session = requests.Session()
        
        # Configurar retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        
        # Configurar mTLS se certificados disponíveis
        if self.mtls_cert_path and self.mtls_key_path:
            try:
                session.cert = (self.mtls_cert_path, self.mtls_key_path)
                
                # Configurar CA bundle
                if self.ca_cert_path:
                    session.verify = self.ca_cert_path
                else:
                    # Usar certifi como fallback
                    session.verify = certifi.where()
            except Exception as e:
                print(f"Warning: Could not configure mTLS: {e}")
                # Continuar sem mTLS em desenvolvimento
        
        return session
    
    @classmethod
    def from_env(cls, consent=None):
        """Cria cliente a partir de variáveis de ambiente."""
        return cls(
            base_url=os.getenv("OF_BASE_URL", ""),
            client_id=os.getenv("OF_CLIENT_ID", ""),
            client_secret=os.getenv("OF_CLIENT_SECRET", ""),
            mtls_cert_path=os.getenv("OF_MTLS_CERT_PATH"),
            mtls_key_path=os.getenv("OF_MTLS_KEY_PATH"),
            ca_cert_path=os.getenv("OF_CA_CERT_PATH"),
        )
    
    def _get_access_token(self, consent_id: Optional[str] = None) -> Optional[str]:
        """
        Obtém access token OAuth2.
        
        Args:
            consent_id: ID do consentimento (opcional, para escopo específico)
            
        Returns:
            Access token ou None se falhar
        """
        # Verificar se token ainda é válido
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=5):
                return self._access_token
        
        # Obter novo token
        token_url = f"{self.base_url}/oauth/token"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        if consent_id:
            data["scope"] = f"consents:{consent_id}"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        try:
            response = self._session.post(token_url, data=data, headers=headers)
            response.raise_for_status()
            
            token_data = response.json()
            self._access_token = token_data.get("access_token")
            
            # Calcular expiração (default: 1 hora)
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            return self._access_token
        except Exception as e:
            print(f"Error obtaining access token: {e}")
            return None
    
    def _get_headers(self, consent_id: Optional[str] = None) -> Dict[str, str]:
        """Obtém headers HTTP com autenticação."""
        token = self._get_access_token(consent_id)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        return headers
    
    def create_consent(
        self,
        user_id: str,
        scopes: List[str],
        expiration_date: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Cria um consentimento Open Finance.
        
        Args:
            user_id: ID do usuário
            scopes: Lista de escopos (ex: ["payments", "accounts"])
            expiration_date: Data de expiração do consentimento
            
        Returns:
            Dados do consentimento criado ou None se falhar
        """
        consent_url = f"{self.base_url}/open-banking/consents/v1/consents"
        
        if expiration_date is None:
            expiration_date = datetime.now() + timedelta(days=90)
        
        payload = {
            "data": {
                "loggedUser": {
                    "document": {
                        "identification": user_id,
                        "rel": "CPF"
                    }
                },
                "businessEntity": {
                    "document": {
                        "identification": self.client_id,
                        "rel": "CNPJ"
                    }
                },
                "permissions": scopes,
                "expirationDateTime": expiration_date.isoformat()
            }
        }
        
        try:
            response = self._session.post(
                consent_url,
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error creating consent: {e}")
            return None
    
    def get_consent(self, consent_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém dados de um consentimento.
        
        Args:
            consent_id: ID do consentimento
            
        Returns:
            Dados do consentimento ou None se falhar
        """
        if self._is_mock:
            return {
                "data": {
                    "consentId": consent_id,
                    "status": "ACTIVE",
                    "expirationDateTime": (datetime.now() + timedelta(days=90)).isoformat(),
                }
            }

        consent_url = f"{self.base_url}/open-banking/consents/v1/consents/{consent_id}"

        try:
            response = self._session.get(
                consent_url,
                headers=self._get_headers(consent_id)
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting consent: {e}")
            return None
    
    def create_pix_payment(
        self,
        consent_id: str,
        cpf: str,
        pix_key: str,
        amount_brl: str,
        description: str = "",
        end_to_end_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria um pagamento Pix via Payments Initiation API.
        
        Args:
            consent_id: ID do consentimento
            cpf: CPF do pagador
            pix_key: Chave Pix do beneficiário
            amount_brl: Valor em BRL (string)
            description: Descrição do pagamento
            end_to_end_id: ID end-to-end (opcional, gerado se não fornecido)
            
        Returns:
            Dados da transação Pix criada
        """
        if self._is_mock:
            e2e = end_to_end_id or f"E{datetime.now().strftime('%Y%m%d%H%M%S')}{cpf[-4:]}"
            txid = f"mock_txid_{uuid.uuid4().hex[:12]}"
            return {
                "txid": txid,
                "status": "SETTLED",
                "amount": amount_brl,
                "currency": "BRL",
                "created_at": datetime.now().isoformat(),
                "paymentId": e2e,
            }

        payment_url = f"{self.base_url}/open-banking/payments/v1/pix/payments"

        if not end_to_end_id:
            # Gerar E2E ID único
            end_to_end_id = f"E{datetime.now().strftime('%Y%m%d%H%M%S')}{cpf[-4:]}"
        
        payload = {
            "data": {
                "payment": {
                    "paymentId": end_to_end_id,
                    "amount": amount_brl,
                    "currency": "BRL",
                    "paymentMethod": "PIX",
                    "debtorAccount": {
                        "identification": cpf,
                        "name": "Pagador"
                    },
                    "creditorAccount": {
                        "identification": pix_key,
                        "name": "Beneficiário"
                    },
                    "remittanceInformation": description or f"Pagamento via PayPi-Bridge"
                }
            }
        }
        
        try:
            response = self._session.post(
                payment_url,
                json=payload,
                headers=self._get_headers(consent_id)
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extrair informações relevantes
            payment_data = result.get("data", {}).get("payment", {})
            
            return {
                "txid": payment_data.get("paymentId", end_to_end_id),
                "status": payment_data.get("status", "PENDING"),
                "amount": amount_brl,
                "currency": "BRL",
                "created_at": datetime.now().isoformat(),
                "raw_response": result
            }
        except requests.exceptions.HTTPError as e:
            error_detail = "Unknown error"
            try:
                error_response = e.response.json()
                error_detail = error_response.get("errors", [{}])[0].get("detail", str(e))
            except:
                error_detail = str(e)
            
            print(f"Error creating Pix payment: {error_detail}")
            return {
                "txid": end_to_end_id,
                "status": "ERROR",
                "error": error_detail,
                "amount": amount_brl
            }
        except Exception as e:
            print(f"Unexpected error creating Pix payment: {e}")
            return {
                "txid": end_to_end_id,
                "status": "ERROR",
                "error": str(e),
                "amount": amount_brl
            }
    
    def get_payment_status(
        self,
        consent_id: str,
        payment_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém status de um pagamento Pix.
        
        Args:
            consent_id: ID do consentimento
            payment_id: ID do pagamento
            
        Returns:
            Status do pagamento ou None se falhar
        """
        payment_url = f"{self.base_url}/open-banking/payments/v1/pix/payments/{payment_id}"
        
        try:
            response = self._session.get(
                payment_url,
                headers=self._get_headers(consent_id)
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting payment status: {e}")
            return None
    
    def get_accounts(
        self,
        consent_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Obtém lista de contas bancárias.
        
        Args:
            consent_id: ID do consentimento
            
        Returns:
            Lista de contas ou None se falhar
        """
        if self._is_mock:
            return []

        accounts_url = f"{self.base_url}/open-banking/accounts/v1/accounts"

        try:
            response = self._session.get(
                accounts_url,
                headers=self._get_headers(consent_id)
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("data", {}).get("account", [])
        except Exception as e:
            print(f"Error getting accounts: {e}")
            return None
    
    def get_account_transactions(
        self,
        consent_id: str,
        account_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Obtém transações de uma conta.
        
        Args:
            consent_id: ID do consentimento
            account_id: ID da conta
            from_date: Data inicial (opcional)
            to_date: Data final (opcional)
            
        Returns:
            Lista de transações ou None se falhar
        """
        transactions_url = f"{self.base_url}/open-banking/accounts/v1/accounts/{account_id}/transactions"
        
        params = {}
        if from_date:
            params["fromBookingDateTime"] = from_date.isoformat()
        if to_date:
            params["toBookingDateTime"] = to_date.isoformat()
        
        try:
            response = self._session.get(
                transactions_url,
                params=params,
                headers=self._get_headers(consent_id)
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("data", {}).get("transaction", [])
        except Exception as e:
            print(f"Error getting transactions: {e}")
            return None
    
    def reconcile_payment(
        self,
        consent_id: str,
        account_id: str,
        expected_amount: str,
        expected_txid: Optional[str] = None,
        from_date: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Reconcilia um pagamento verificando transações da conta.
        
        Args:
            consent_id: ID do consentimento
            account_id: ID da conta
            expected_amount: Valor esperado
            expected_txid: ID da transação esperado (opcional)
            from_date: Data inicial para busca (opcional)
            
        Returns:
            Dados da reconciliação ou None se não encontrado
        """
        if self._is_mock:
            return {
                "found": True,
                "transaction": {"transactionId": f"mock_tx_{uuid.uuid4().hex[:8]}", "amount": {"amount": expected_amount}},
                "matched_by": "amount",
            }

        if from_date is None:
            from_date = datetime.now() - timedelta(days=1)

        transactions = self.get_account_transactions(
            consent_id,
            account_id,
            from_date=from_date
        )
        
        if not transactions:
            return None
        
        # Buscar transação que corresponde
        for tx in transactions:
            tx_amount = str(tx.get("amount", {}).get("amount", ""))
            
            # Verificar por valor
            if tx_amount == expected_amount:
                # Se txid fornecido, verificar também
                if expected_txid:
                    tx_id = tx.get("transactionId") or tx.get("endToEndId", "")
                    if expected_txid in tx_id:
                        return {
                            "found": True,
                            "transaction": tx,
                            "matched_by": "amount_and_txid"
                        }
                else:
                    return {
                        "found": True,
                        "transaction": tx,
                        "matched_by": "amount"
                    }
        
        return {
            "found": False,
            "searched_transactions": len(transactions)
        }
