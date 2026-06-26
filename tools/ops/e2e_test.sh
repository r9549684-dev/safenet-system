#!/bin/bash
BASE="https://safenetsystem.duckdns.org"
CB_TOKEN=$(grep '^CRYPTOBOT_TOKEN=' /opt/safenet-v2/infra/.env | cut -d'=' -f2-)

echo "=== STEP 1: Auth ==="
TOKEN_RESP=$(curl -s -X POST "$BASE/auth/device" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test-e2e-v3-001","country":"RU"}')
JWT=$(echo "$TOKEN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "JWT OK"

echo ""
echo "=== STEP 2: Create invoice ==="
INV_RESP=$(curl -s -X POST "$BASE/payments/cryptobot/invoice" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT" \
  -d '{"amount":10,"months":1}')
echo "Response: $INV_RESP"
INVOICE_ID=$(echo "$INV_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('invoice_id','ERR'))")
PAY_URL=$(echo "$INV_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('pay_url','ERR'))")
echo ">>> invoice_id: $INVOICE_ID"
echo ">>> pay_url:    $PAY_URL"

echo ""
echo "=== STEP 3: /users/me before payment ==="
curl -s "$BASE/users/me" -H "Authorization: Bearer $JWT"
echo ""

echo ""
echo "=== STEP 4: Webhook with correct HMAC signature ==="

# Тело вебхука — одна строка JSON без trailing newline
printf '{"update_id":999003,"update_type":"invoice_paid","request_date":"2026-02-20T05:00:00Z","payload":{"invoice_id":"%s","hash":"testhash","currency_type":"crypto","currency":"USDT","amount":"10","paid_amount":"10","paid_asset":"USDT","status":"paid","payload":""}}' \
  "$INVOICE_ID" > /tmp/wh.json

echo "Webhook body:"
cat /tmp/wh.json
echo ""

# Подпись через отдельный скрипт (без конкуренции за stdin)
SIGNATURE=$(python3 /tmp/gen_sig.py "$CB_TOKEN" /tmp/wh.json)
echo "Signature: $SIGNATURE"

WH_RESP=$(curl -s -X POST "$BASE/payments/cryptobot/webhook" \
  -H "Content-Type: application/json" \
  -H "Crypto-Pay-Signature: $SIGNATURE" \
  --data-binary @/tmp/wh.json)
echo "Webhook response: $WH_RESP"

echo ""
echo "=== STEP 5: /users/me after webhook ==="
ME=$(curl -s "$BASE/users/me" -H "Authorization: Bearer $JWT")
echo "Response: $ME"

IS_PREMIUM=$(echo "$ME" | python3 -c "import sys,json; print(json.load(sys.stdin).get('is_premium','?'))")
UNTIL=$(echo "$ME" | python3 -c "import sys,json; print(json.load(sys.stdin).get('premium_until','?'))")

echo ""
echo "=== RESULT ==="
echo "is_premium:    $IS_PREMIUM"
echo "premium_until: $UNTIL"

if [ "$IS_PREMIUM" = "True" ] || [ "$IS_PREMIUM" = "true" ]; then
  echo "E2E TEST PASSED"
else
  echo "E2E TEST FAILED"
  exit 1
fi
