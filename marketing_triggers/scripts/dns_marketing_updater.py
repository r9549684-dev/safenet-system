import json
import os
import sys
import base64
import hashlib
from cryptography.fernet import Fernet

# Добавляем путь для импорта из dns_messenger, если нужно, или реализуем локально
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'dns_messenger', 'scripts')))
import dns_updater

def get_user_fernet_key(user_secret: str) -> Fernet:
    """Генерирует уникальный ключ шифрования на основе секрета конкретного пользователя."""
    seed = user_secret.encode('utf-8')
    derived_key = base64.urlsafe_b64encode(hashlib.sha256(seed).digest())
    return Fernet(derived_key)

def encrypt_for_user(data: str, user_secret: str) -> str:
    """Шифрует сообщение индивидуальным ключом пользователя для безопасности."""
    f = get_user_fernet_key(user_secret)
    return f.encrypt(data.encode('utf-8')).decode('utf-8')

def send_trigger_to_dns(user_id: str, message: str, user_secret: str, config_path: str = None) -> bool:
    """
    Упаковывает персональный триггер и обновляет специальную DNS-запись для пользователя.
    В реальной системе это может быть поддомен вида <user_id>.triggers.safenet-mesh.net
    """
    if config_path is None:
        # Fallback на дефолтный config
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'triggers_config.json')
        
    encrypted_payload = encrypt_for_user(message, user_secret)
    
    # Имитация вызова API провайдера DNS для обновления персональной записи
    # В реальности: subdomain = f"{user_id}.triggers.safenet-mesh.net"
    subdomain = f"{user_id}.triggers.safenet-mesh.net"
    
    print(f"[MARKETING] Отправка персонального триггера в DNS для {subdomain}...")
    
    # Используем тот же механизм, что и в dns_updater, но с поддоменом
    url = f"https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records"
    headers = {"Authorization": "Bearer MOCK_API_TOKEN", "Content-Type": "application/json"}
    data = {
        "type": "TXT", 
        "name": subdomain, 
        "content": encrypted_payload, 
        "ttl": 60  # Очень короткий TTL для мгновенной доставки пушей
    }
    
    try:
        import requests
        response = requests.post(url, headers=headers, json=data, timeout=10)
        return response.status_code == 200 and response.json().get("success", False)
    except Exception as e:
        print(f"[ERROR] Failed to update user DNS record: {e}")
        return False

def update_user_dns_record(user_id: str, message: str) -> bool:
    """Обертка для тестов, использующая заглушку секрета."""
    return send_trigger_to_dns(user_id, message, user_secret=f"secret_{user_id}")