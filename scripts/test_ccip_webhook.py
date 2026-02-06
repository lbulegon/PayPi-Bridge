#!/usr/bin/env python3
"""
Gera X-Signature HMAC e opcionalmente envia POST para /api/webhooks/ccip.
Uso:
  export CCIP_WEBHOOK_SECRET=seu-secret
  python scripts/test_ccip_webhook.py
  python scripts/test_ccip_webhook.py --send http://localhost:9080
  python scripts/test_ccip_webhook.py --intent-id pi_123 --event-id evt_1
"""
import argparse
import hmac
import hashlib
import json
import os
import sys

try:
    import requests
except ImportError:
    requests = None


def main():
    ap = argparse.ArgumentParser(description="Testar webhook CCIP (HMAC + payload)")
    ap.add_argument("--secret", default=os.getenv("CCIP_WEBHOOK_SECRET", "replace-with-random-hmac"), help="Secret para HMAC")
    ap.add_argument("--intent-id", default="pi_1734567890123", help="intent_id do payload")
    ap.add_argument("--event-id", default="evt_test_001", help="event_id (idempotência)")
    ap.add_argument("--brl-amount", default="50.00", help="fx_quote.brl_amount")
    ap.add_argument("--status", default="CONFIRMED", help="status do intent")
    ap.add_argument("--send", metavar="BASE_URL", help="Enviar POST para BASE_URL/api/webhooks/ccip")
    args = ap.parse_args()

    payload = {
        "intent_id": args.intent_id,
        "event_id": args.event_id,
        "fx_quote": {"brl_amount": args.brl_amount},
        "status": args.status,
    }
    body = json.dumps(payload, separators=(",", ":"))
    signature = hmac.new(args.secret.encode(), body.encode(), hashlib.sha256).hexdigest()

    print("Body (raw):", body)
    print("X-Signature:", signature)
    print()
    print("curl example:")
    print(
        f'  curl -X POST {args.send or "http://localhost:9080"}/api/webhooks/ccip \\'
    )
    print('    -H "Content-Type: application/json" \\')
    print(f'    -H "X-Signature: {signature}" \\')
    print(f"    -d '{body}'")
    print()

    if args.send:
        if not requests:
            print("Install requests to use --send: pip install requests", file=sys.stderr)
            sys.exit(1)
        url = args.send.rstrip("/") + "/api/webhooks/ccip"
        r = requests.post(url, data=body, headers={"Content-Type": "application/json", "X-Signature": signature})
        print(f"Response {r.status_code}:", r.text)
        sys.exit(0 if r.ok else 1)


if __name__ == "__main__":
    main()
