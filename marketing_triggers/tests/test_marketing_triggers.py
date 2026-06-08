import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

class TestMarketingTriggers(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.base_dir, '..', 'config', 'triggers_config.json')
        self.dns_config_path = os.path.join(self.base_dir, '..', '..', 'dns_messenger', 'config', 'dns_config.json')
        
        self.mock_config = {
            "bandwidth_threshold_mbps": 5.0,
            "days_before_expiry_alert": 3,
            "marketing_offers": {
                "single_device": "Подключите 2 устройства всего за 100₽ в месяц!"
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.mock_config, f)

    def test_01_technical_trigger_activation(self):
        """Тест 1: Срабатывание технического триггера (падение скорости)"""
        import trigger_engine
        import dns_marketing_updater
        
        engine = trigger_engine.TriggerEngine(self.config_path)
        
        # Эмуляция падения скорости
        user_id = "user_123"
        current_speed = 2.0 # Ниже порога 5.0
        
        message = engine.evaluate_technical_state(user_id, current_speed)
        self.assertIsNotNone(message)
        self.assertIn("выделенный скоростной шлюз", message)
        
        # Проверяем, что сообщение успешно упаковано и отправлено в DNS
        with patch('dns_marketing_updater.send_trigger_to_dns') as mock_send:
            mock_send.return_value = True
            success = dns_marketing_updater.send_trigger_to_dns(user_id, message, "mock_secret")
            self.assertTrue(success)
            mock_send.assert_called_once_with(user_id, message, "mock_secret")

    def test_02_push_delivery_in_isolation(self):
        """Тест 2: Доставка пуша в изоляции (только DNS работает)"""
        import marketing_client
        
        client = marketing_client.MarketingClient(self.dns_config_path)
        user_id = "user_123"
        user_secret = "user_specific_secret_key_123"
        
        # Искусственное сообщение от сервера
        server_message = "Ваша подписка истекает через 3 дня. Продлите сейчас со скидкой 20%!"
        
        # Эмуляция DNS-ответа с зашифрованными данными
        encrypted_payload = client._encrypt_for_user(server_message, user_secret)
        
        with patch('marketing_client.dns.resolver.resolve') as mock_dns:
            mock_dns.return_value = [MagicMock(to_text=lambda: f'"{encrypted_payload}"')]
            
            # Симуляция работы клиента при отключенном HTTP
            received_message = client.fetch_and_decrypt_marketing_message(user_id, user_secret)
            
            self.assertEqual(received_message, server_message)
            mock_dns.assert_called_once()

    def test_03_personal_trigger_security(self):
        """Тест 3: Безопасность персональных триггеров (один пользователь не читает чужое)"""
        import marketing_client
        
        client = marketing_client.MarketingClient(self.dns_config_path)
        user_a_secret = "secret_key_user_A"
        user_b_secret = "secret_key_user_B"
        
        private_message_for_A = "Ваш персональный код на скидку: PROMO_A"
        
        # Сервер шифрует сообщение для пользователя А
        encrypted_for_A = client._encrypt_for_user(private_message_for_A, user_a_secret)
        
        # Пользователь Б пытается расшифровать это сообщение своим ключом
        with self.assertRaises(Exception): # Fernet выбросит InvalidToken
            client._decrypt_for_user(encrypted_for_A, user_b_secret)
            
        # Пользователь А успешно расшифровывает
        decrypted_by_A = client._decrypt_for_user(encrypted_for_A, user_a_secret)
        self.assertEqual(decrypted_by_A, private_message_for_A)

if __name__ == '__main__':
    unittest.main()