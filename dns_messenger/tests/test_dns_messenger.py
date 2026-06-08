import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

class TestDNSMessenger(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.base_dir, '..', 'config', 'dns_config.json')
        
        self.mock_config = {
            "domain": "status.safenet-mesh.net",
            "secret_key": "super_secret_aes_256_key_for_testing_123",
            "dns_servers": ["8.8.8.8", "1.1.1.1"]
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.mock_config, f)

    def test_01_artificial_isolation(self):
        """Тест 1: Искусственная изоляция - HTTP заблокирован, но DNS работает"""
        import dns_client
        import dns_updater
        
        # 1. Проверяем, что стандартный HTTP канал заблокирован
        with patch('dns_client.requests.get') as mock_http:
            mock_http.side_effect = Exception("HTTP blocked by firewall")
            with self.assertRaises(Exception) as context:
                dns_client.fetch_standard_data(self.config_path)
            self.assertIn("blocked", str(context.exception).lower())
            
        # 2. Проверяем, что экстренный DNS канал работает несмотря на блокировку HTTP
        encrypted_payload = dns_updater.encrypt_data('{"gateways": ["1.2.3.4"]}', self.config_path)
        
        with patch('dns.resolver.resolve') as mock_dns:
            mock_dns.return_value = [MagicMock(to_text=lambda: f'"{encrypted_payload}"')]
            
            result = dns_client.fetch_emergency_data(self.config_path)
            self.assertEqual(result, '{"gateways": ["1.2.3.4"]}')
            mock_dns.assert_called_once()

    def test_02_encryption_decryption_integrity(self):
        """Тест 2: Шифрование и расшифровка - данные не теряются"""
        import dns_updater
        import dns_client
        
        original_data = {"ip": "198.51.100.10", "status": "active", "message": "URGENT: Switch to backup node"}
        original_json = json.dumps(original_data)
        
        encrypted = dns_updater.encrypt_data(original_json, self.config_path)
        decrypted = dns_client.decrypt_data(encrypted, self.config_path)
        
        self.assertEqual(decrypted, original_json)
        parsed = json.loads(decrypted)
        self.assertEqual(parsed["ip"], "198.51.100.10")
        self.assertEqual(parsed["message"], "URGENT: Switch to backup node")

    def test_03_auto_background_update(self):
        """Тест 3: Автоматическое фоновое обновление - Мастер обновляет TXT при смене IP"""
        import dns_updater
        
        new_gateway_ip = "203.0.113.50"
        payload = {"gateways": [new_gateway_ip]}
        
        with patch('dns_updater.requests.post') as mock_api:
            mock_api.return_value.status_code = 200
            mock_api.return_value.json.return_value = {"success": True}
            
            success = dns_updater.update_dns_record(self.config_path, payload)
            
            self.assertTrue(success)
            mock_api.assert_called_once()
            call_kwargs = mock_api.call_args[1]
            self.assertIn("content", call_kwargs["json"])
            # Проверяем, что контент зашифрован (Fernet начинается с gAAAAA)
            self.assertTrue(call_kwargs["json"]["content"].startswith("gAAAAA"))

if __name__ == '__main__':
    unittest.main()