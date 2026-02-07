"""
Adapters do PPBridge Service.
"""
from .base import CryptoAdapter, FinanceAdapter, AdapterError
from .crypto_pi_stub import PiNetworkStubAdapter
from .finance_pix_stub import PixStubAdapter

__all__ = [
    'CryptoAdapter',
    'FinanceAdapter',
    'AdapterError',
    'PiNetworkStubAdapter',
    'PixStubAdapter',
]


def get_adapter(domain: str, adapter_type: str):
    """
    Factory para obter adapter baseado em domain e type.
    
    Args:
        domain: "crypto" ou "finance"
        adapter_type: tipo do adapter (ex: "pi_network", "pix")
    
    Returns:
        Instância do adapter apropriado
    """
    if domain == "crypto":
        if adapter_type == "pi_network":
            return PiNetworkStubAdapter()
        elif adapter_type == "eth":
            # TODO: Implementar EthereumStubAdapter
            raise NotImplementedError(f"Adapter {adapter_type} not implemented")
        else:
            raise ValueError(f"Unknown crypto adapter: {adapter_type}")
    
    elif domain == "finance":
        if adapter_type == "pix":
            return PixStubAdapter()
        elif adapter_type == "bank":
            # TODO: Implementar BankStubAdapter
            raise NotImplementedError(f"Adapter {adapter_type} not implemented")
        else:
            raise ValueError(f"Unknown finance adapter: {adapter_type}")
    
    else:
        raise ValueError(f"Unknown domain: {domain}")
