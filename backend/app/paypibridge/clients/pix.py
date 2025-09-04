from .open_finance import OpenFinanceClient

class PixClient:
    def __init__(self, of: OpenFinanceClient, consent=None):
        self.of = of
        self.consent = consent

    @classmethod
    def from_env(cls, consent=None):
        return cls(OpenFinanceClient.from_env(), consent)

    def create_immediate_payment(self, cpf: str, pix_key: str, amount_brl: str, description: str = "") -> dict:
        return self.of.create_pix_payment(cpf=cpf, pix_key=pix_key, amount_brl=amount_brl, description=description)
