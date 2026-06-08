import json
import os
import base64
import hashlib
import requests
from cryptography.fernet import Fernet

def get_fernet_key(config_path: str) -> Fernet:
    """Получает или генерирует ключ шифрования на основе секрета из конфига."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    # Деривируем 32-байтовый ключ для Fernet (требует url-safe base64)
    seed = config["secret_key"].encode('utf-8')
    derived_key = base64.urlsafe_b64encode(hashlib.sha256(seed).digest())
    return Fernet(derived_key)

def encrypt_data(data: str, config_path: str) -> str:
    """Шифрует строковые данные для безопасной передачи через DNS TXT."""
    f = get_fernet_key(config_path)
    return f.encrypt(data.encode('utf-8')).decode('utf-8')

def update_dns_record(config_path: str, payload: dict) -> bool:
    """
    Автоматическое фоновое обновление: упаковывает данные и обновляет TXT-запись 
    через API провайдера DNS (например, Cloudflare).
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    data_str = json.dumps(payload)
    encrypted_txt = encrypt_data(data_str, config_path)
    
    domain = config["domain"]
    # Имитация вызова API провайдера DNS (Cloudflare)
    url = f"https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records"
    headers = {"Authorization": "Bearer MOCK_API_TOKEN", "Content-Type": "application/json"}
    data = {
        "type": "TXT", 
        "name": domain, 
        "content": encrypted_txt, 
        "ttl": 300  # Короткий TTL для быстрой доставки экстренных сообщений
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        return response.status_code == 200 and response.json().get("success", False)
    except Exception as e:
        print(f"[ERROR] Failed to update DNS record: {e}")
        return False

if __name__ == "__main__":
    # Демо-запуск обновления
    config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'dns_config.json')
    if os.path.exists(config_file):
        print("[INFO] Updating DNS record with new gateway IP...")
        success = update_dns_record(config_file, {"gateways": ["203.0.113.50"], "status": "rotated"})
        print(f"[RESULT] Update successful: {success}")