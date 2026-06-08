import os
import sys
import json
import dns.resolver
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken

class MarketingClient:
    def __init__(self, dns_config_path: str):
        self.dns_config_path = dns_config_path
        with open(dns_config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def _get_user_fernet_key(self, user_secret: str) -> Fernet:
        """Восстанавливает ключ шифрования пользователя."""
        seed = user_secret.encode('utf-8')
        derived_key = base64.urlsafe_b64encode(hashlib.sha256(seed).digest())
        return Fernet(derived_key)

    def _encrypt_for_user(self, data: str, user_secret: str) -> str:
        """Шифрует сообщение (используется в тестах для генерации мок-ответа сервера)."""
        f = self._get_user_fernet_key(user_secret)
        return f.encrypt(data.encode('utf-8')).decode('utf-8')

    def _decrypt_for_user(self, encrypted_b64: str, user_secret: str) -> str:
        """Расшифровывает сообщение индивидуальным ключом. Выбросит InvalidToken при чужом ключе."""
        f = self._get_user_fernet_key(user_secret)
        return f.decrypt(encrypted_b64.encode('utf-8')).decode('utf-8')

    def fetch_and_decrypt_marketing_message(self, user_id: str, user_secret: str) -> str:
        """
        Клиентский модуль: читает маркетинговые записи из DNS по специфичному поддомену пользователя
        и расшифровывает их, работая даже при отключенном HTTP (только сырой DNS).
        """
        subdomain = f"{user_id}.triggers.safenet-mesh.net"
        
        try:
            # Прямой DNS-запрос в обход локального резолвера провайдера
            answers = dns.resolver.resolve(subdomain, 'TXT', lifetime=5)
            
            # Извлекаем текст записи
            txt_record = answers[0].to_text().strip('"')
            
            return self._decrypt_for_user(txt_record, user_secret)
        except InvalidToken:
            raise Exception("SECURITY ALERT: Попытка расшифровки чужим ключом или повреждение данных!")
        except dns.resolver.NXDOMAIN:
            return "" # Нет новых сообщений
        except dns.resolver.Timeout:
            raise Exception("DNS query timed out")
        except Exception as e:
            raise Exception(f"Marketing DNS fetch failed: {e}")

    def display_push_if_any(self, user_id: str, user_secret: str) -> dict:
        """UX-метод: если есть сообщение, возвращает его для отображения в интерфейсе 'одной кнопкой'."""
        try:
            message = self.fetch_and_decrypt_marketing_message(user_id, user_secret)
            if message:
                return {
                    "show_push": True,
                    "title": "🔔 Важное обновление SafeNet",
                    "body": message,
                    "action_button": "Применить"
                }
        except Exception:
            # В случае сбоя DNS мы просто не показываем пуш, чтобы не пугать пользователя
            pass
            
        return {"show_push": False}