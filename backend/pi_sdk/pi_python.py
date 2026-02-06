# -*- coding: utf-8 -*-
"""
Pi Network SDK - cópia para PayPi-Bridge (Docker).
Original: https://github.com/pi-apps/pi-python
"""

import requests
import json
import stellar_sdk as s_sdk


class PiNetwork:
    api_key = ""
    client = ""
    account = ""
    base_url = ""
    from_address = ""
    open_payments = {}
    network = ""
    server = ""
    keypair = ""
    fee = ""

    def initialize(self, api_key, wallet_private_key, network):
        try:
            if not self.validate_private_seed_format(wallet_private_key):
                print("No valid private seed!")
            self.api_key = api_key
            self.load_account(wallet_private_key, network)
            self.base_url = "https://api.minepi.com"
            self.open_payments = {}
            self.network = network
            self.fee = self.server.fetch_base_fee()
        except Exception:
            return False

    def get_balance(self):
        try:
            balances = self.server.accounts().account_id(self.keypair.public_key).call()["balances"]
            for i in balances:
                if i["asset_type"] == "native":
                    return float(i["balance"])
            return 0
        except Exception:
            return 0

    def get_payment(self, payment_id):
        url = self.base_url + "/v2/payments/" + payment_id
        re = requests.get(url, headers=self.get_http_headers())
        return self.handle_http_response(re)

    def create_payment(self, payment_data):
        try:
            if not self.validate_payment_data(payment_data):
                if __debug__:
                    print("No valid payments found. Creating a new one...")

            balances = self.server.accounts().account_id(self.keypair.public_key).call()["balances"]
            balance_found = False
            for i in balances:
                if i["asset_type"] == "native":
                    balance_found = True
                    if (float(payment_data["amount"]) + (float(self.fee) / 10000000)) > float(i["balance"]):
                        return ""
                    break

            if balance_found is False:
                return ""

            obj = {"payment": payment_data}
            obj_str = json.dumps(obj)
            url = self.base_url + "/v2/payments"
            res = requests.post(url, data=obj_str, json=obj, headers=self.get_http_headers())
            parsed_response = self.handle_http_response(res)

            identifier = ""
            if parsed_response and "error" in parsed_response:
                identifier = parsed_response.get("payment", {}).get("identifier", "")
            elif parsed_response:
                identifier = parsed_response.get("identifier", "")

            if identifier:
                self.open_payments[identifier] = parsed_response or {}
            return identifier
        except Exception:
            return ""

    def submit_payment(self, payment_id, pending_payment):
        if payment_id not in self.open_payments:
            return False
        if pending_payment is False or payment_id in self.open_payments:
            payment = self.open_payments[payment_id]
        else:
            payment = pending_payment

        balances = self.server.accounts().account_id(self.keypair.public_key).call()["balances"]
        balance_found = False
        for i in balances:
            if i["asset_type"] == "native":
                balance_found = True
                if (float(payment["amount"]) + (float(self.fee) / 10000000)) > float(i["balance"]):
                    return ""
                break

        if balance_found is False:
            return ""

        if __debug__:
            print("Debug_Data: Payment information\n" + str(payment))

        self.set_horizon_client(payment["network"])
        transaction = self.build_a2u_transaction(payment)
        txid = self.submit_transaction(transaction)
        if payment_id in self.open_payments:
            del self.open_payments[payment_id]
        return txid

    def complete_payment(self, identifier, txid):
        obj = {"txid": txid} if txid else {}
        obj_str = json.dumps(obj)
        url = self.base_url + "/v2/payments/" + identifier + "/complete"
        re = requests.post(url, data=obj_str, json=obj, headers=self.get_http_headers())
        return self.handle_http_response(re)

    def cancel_payment(self, identifier):
        obj = {}
        obj_str = json.dumps(obj)
        url = self.base_url + "/v2/payments/" + identifier + "/cancel"
        re = requests.post(url, data=obj_str, json=obj, headers=self.get_http_headers())
        return self.handle_http_response(re)

    def get_incomplete_server_payments(self):
        url = self.base_url + "/v2/payments/incomplete_server_payments"
        re = requests.get(url, headers=self.get_http_headers())
        res = self.handle_http_response(re)
        if not res:
            res = {"incomplete_server_payments": []}
        return res.get("incomplete_server_payments", [])

    def get_http_headers(self):
        return {"Authorization": "Key " + self.api_key, "Content-Type": "application/json"}

    def handle_http_response(self, re):
        try:
            result = re.json()
            return json.loads(json.dumps(result))
        except Exception:
            return False

    def set_horizon_client(self, network):
        self.client = self.server

    def load_account(self, private_seed, network):
        self.keypair = s_sdk.Keypair.from_secret(private_seed)
        if network == "Pi Network":
            horizon = "https://api.mainnet.minepi.com"
        else:
            horizon = "https://api.testnet.minepi.com"
        self.server = s_sdk.Server(horizon)
        self.account = self.server.load_account(self.keypair.public_key)

    def build_a2u_transaction(self, transaction_data):
        if not self.validate_payment_data(transaction_data):
            print("No valid transaction!")
        amount = str(transaction_data["amount"])
        fee = self.fee
        to_address = transaction_data["to_address"]
        memo = transaction_data["identifier"]
        transaction = (
            s_sdk.TransactionBuilder(
                source_account=self.account,
                network_passphrase=self.network,
                base_fee=fee,
            )
            .add_text_memo(memo)
            .append_payment_op(to_address, s_sdk.Asset.native(), amount)
            .set_timeout(180)
            .build()
        )
        return transaction

    def submit_transaction(self, transaction):
        transaction.sign(self.keypair)
        response = self.server.submit_transaction(transaction)
        return response["id"]

    def validate_payment_data(self, data):
        """Para criar pagamento: amount, memo, metadata, uid (ou user_uid). Para submit: identifier, to_address."""
        if not data or "amount" not in data or "memo" not in data or "metadata" not in data:
            return False
        if "identifier" in data and "to_address" in data:
            return True
        if "uid" in data or "user_uid" in data:
            return True
        return False

    def validate_private_seed_format(self, seed):
        if not seed or not str(seed).upper().startswith("S"):
            return False
        return len(seed) == 56
