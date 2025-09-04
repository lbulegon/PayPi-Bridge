import hmac, hashlib, os, json, requests

def sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

def notify_backend(url: str, payload: dict):
    secret = os.getenv("CCIP_WEBHOOK_SECRET", "")
    body = json.dumps(payload).encode()
    sig = sign(body, secret)
    return requests.post(
        url,
        data=body,
        headers={"Content-Type": "application/json", "X-Signature": sig},
        timeout=10
    )
