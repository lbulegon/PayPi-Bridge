import os, requests

class OpenFinanceClient:
    """
    Placeholder Open Finance client.
    Em produção: mTLS, OAuth2, consents por escopo e endpoints do ASPSP.
    """
    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret

    @classmethod
    def from_env(cls):
        return cls(
            base_url=os.getenv("OF_BASE_URL", ""),
            client_id=os.getenv("OF_CLIENT_ID", ""),
            client_secret=os.getenv("OF_CLIENT_SECRET", ""),
        )

    def create_pix_payment(self, **kwargs) -> dict:
        # Simula chamada (substituir por implementação real)
        return {"txid": "E2E-" + kwargs.get("cpf","000"), "status": "SENT"}
