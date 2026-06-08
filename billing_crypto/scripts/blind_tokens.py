import secrets
import hashlib
import time
import json

def generate_blind_token(tariff: str, secret: str, duration_seconds: int = 3600) -> str:
    """
    Генерирует слепой криптографический токен (HMAC-based).
    Токен не содержит персональных данных и проверяется stateless.
    """
    token_raw = secrets.token_hex(16)
    expiry = int(time.time()) + duration_seconds
    payload = f"{token_raw}:{tariff}:{expiry}"
    signature = hashlib.sha256(f"{payload}:{secret}".encode('utf-8')).hexdigest()
    return json.dumps({
        "token_id": payload,
        "sig": signature
    })

def validate_token(token_json_str: str, secret: str) -> tuple[bool, dict]:
    """
    Валидирует токен без обращения к центральной базе (stateless проверка подписи).
    Возвращает (is_valid, payload_dict_or_error_dict).
    """
    try:
        data = json.loads(token_json_str)
        token_id = data["token_id"]
        sig = data["sig"]
        
        expected_sig = hashlib.sha256(f"{token_id}:{secret}".encode('utf-8')).hexdigest()
        if not secrets.compare_digest(sig, expected_sig):
            return False, {"error": "Invalid signature"}
            
        parts = token_id.split(":")
        if len(parts) != 3:
            return False, {"error": "Invalid format"}
            
        expiry = int(parts[2])
        if time.time() > expiry:
            return False, {"error": "Token expired"}
            
        return True, {"tariff": parts[1], "expiry": expiry}
    except Exception:
        return False, {"error": "Invalid token data"}