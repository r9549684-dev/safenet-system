#!/bin/bash
BASE="https://safenetsystem.duckdns.org"

echo "=== Auth ==="
TOKEN_RESP=$(curl -s -X POST "$BASE/auth/device" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test-invoice-fix-001","country":"RU"}')
TOKEN=$(echo "$TOKEN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token OK"

echo ""
echo "=== POST /payments/cryptobot/invoice ==="
curl -s -X POST "$BASE/payments/cryptobot/invoice" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"amount":10,"months":1}'
echo ""
