#!/bin/bash
TOKEN=$(grep '^CRYPTOBOT_TOKEN=' /opt/safenet-v2/infra/.env | cut -d'=' -f2-)
echo "Token prefix: ${TOKEN:0:10}..."

echo ""
echo "--- MAINNET (pay.crypt.bot) ---"
curl -s -H "Crypto-Pay-Api-Token: $TOKEN" https://pay.crypt.bot/api/getMe

echo ""
echo "--- TESTNET (testnet-pay.crypt.bot) ---"
curl -s -H "Crypto-Pay-Api-Token: $TOKEN" https://testnet-pay.crypt.bot/api/getMe
echo ""
