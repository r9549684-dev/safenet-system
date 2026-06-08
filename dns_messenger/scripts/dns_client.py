import json
import dns.resolver
import requests
from cryptography.fernet import Fernet
import hashlib
import base64

def get_fernet_key(config_path: str) -> Fernet:
    """Получает ключ шифрования, идентичный используемому на Мастер-ноде."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    seed = config["secret_key"].encode('utf-8')
    derived_key = base64.urlsafe_b64encode(hashlib.sha256(seed).digest())
    return Fernet(derived_key)

def decrypt_data(encrypted_b64: str, config_path: str) -> str:
    """Расшифровывает данные, полученные из DNS TXT записи."""
    f = get_fernet_key(config_path)
    return f.decrypt(encrypted_b64.encode('utf-8')).decode('utf-8')

def fetch_standard_data(config_path: str) -> str:
    """
    Стандартный способ получения данных (HTTP/HTTPS). 
    Будет заблокирован в условиях цензуры или изоляции.
    """
    response = requests.get("https://api.safenet-mesh.net/v1/config", timeout=5)
    response.raise_for_status()
    return response.text

def fetch_emergency_data(config_path: str) -> str:
    """
    Модуль чтения «Последней мили»: выполняет прямой запрос к DNS-серверам 
    в обход стандартных фильтров, читает TXT-запись и расшифровывает её.
    В реальном Flutter-клиенте это реализуется через Raw UDP Socket к 8.8.8.8 или 1.1.1.1.
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    domain = config["domain"]
    
    try:
        # Прямой DNS-запрос (в Python эмулируется через dns.resolver)
        # lifetime=5 обеспечивает быстрый таймаут, чтобы не блокировать приложение
        answers = dns.resolver.resolve(domain, 'TXT', lifetime=5)
        
        # Извлекаем текст записи, убирая кавычки, которые добавляет dnspython
        txt_record = answers[0].to_text().strip('"')
        
        return decrypt_data(txt_record, config_path)
    except dns.resolver.NXDOMAIN:
        raise Exception("DNS domain does not exist")
    except dns.resolver.Timeout:
        raise Exception("DNS query timed out")
    except Exception as e:
        raise Exception(f"Emergency DNS fetch failed: {e}")

if __name__ == "__main__":
    # Демо-запуск клиента
    config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'dns_config.json')
    if os.path.exists(config_file):
        print("[INFO] Attempting emergency DNS fetch...")
        try:
            # В демо-режиме это упадет без моков, но показывает структуру вызова
            # data = fetch_emergency_data(config_file)
            # print(f"[SUCCESS] Decrypted data: {data}")
            print("[INFO] DNS client module loaded successfully. Ready for Flutter integration.")
        except Exception as e:
            print(f"[ERROR] {e}")