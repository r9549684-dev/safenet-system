#!/usr/bin/env python3
"""
Usage: python3 gen_sig.py <token> <body_file>
Computes HMAC-SHA256(body, SHA256(token)) — CryptoBot webhook signature.
"""
import sys, hmac, hashlib

token = sys.argv[1]
body_file = sys.argv[2]

with open(body_file, "rb") as f:
    body = f.read()

key = hashlib.sha256(token.encode()).digest()
sig = hmac.new(key, body, hashlib.sha256).hexdigest()
print(sig)
