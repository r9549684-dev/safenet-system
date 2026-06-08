import os
import sys
import time
import json
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

class TestBillingCrypto(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.base_dir, '..', 'config', 'billing_config.json')
        self.mock_config = {
            "token_secret": "super_secret_master_key_for_hmac",
            "blockchain_network": "TON",
            "expected_amount_usd": 10.0,
            "confirmations_required": 1,
            "default_token_duration_seconds": 3600
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.mock_config, f)
            
        # In-memory "Central DB" mock
        self.central_db = {}

    def test_01_auto_payment_receipt(self):
        """Тест 1: Автоматический прием платежа и выпуск слепого токена"""
        import blockchain_dispatcher
        import blind_tokens

        mock_tx = {
            "tx_hash": "0x123abc...",
            "amount": 10.0,
            "status": "confirmed",
            "wallet_address": "EQD...mock_wallet"
        }
        
        with patch.object(blockchain_dispatcher.BlockchainDispatcher, 'check_blockchain_api') as mock_api:
            mock_api.return_value = mock_tx
            
            dispatcher = blockchain_dispatcher.BlockchainDispatcher(self.config_path, self.central_db)
            token = dispatcher.process_pending_payment("EQD...mock_wallet")
            
            self.assertIsNotNone(token)
            self.assertIn("token_json", token)
            
            is_valid, _ = blind_tokens.validate_token(token["token_json"], self.mock_config["token_secret"])
            self.assertTrue(is_valid)
            
            self.assertTrue(self.central_db[token["token_json"]]["is_active"])

    def test_02_expiry_control(self):
        """Тест 2: Контроль устаревания и мгновенная блокировка"""
        import blind_tokens
        import access_manager

        short_config = self.mock_config.copy()
        short_config["default_token_duration_seconds"] = 1
        
        token_json = blind_tokens.generate_blind_token("tariff_basic", short_config["token_secret"], 1)
        
        self.central_db[token_json] = {
            "is_active": True,
            "expiry": time.time() + 1,
            "max_devices": 1,
            "active_devices": 0,
            "registered_devices": []
        }
        
        manager = access_manager.AccessManager(self.central_db, short_config["token_secret"])
        
        access_state = manager.check_access(token_json, device_id="device_1")
        self.assertTrue(access_state["allowed"])
        
        time.sleep(1.1)
        
        access_state_expired = manager.check_access(token_json, device_id="device_1")
        self.assertFalse(access_state_expired["allowed"])
        self.assertIn("dns_payment_channel", access_state_expired.get("redirect_to", ""))

    def test_03_replay_protection(self):
        """Тест 3: Защита от повторного использования (фрод)"""
        import blind_tokens
        import access_manager

        token_json = blind_tokens.generate_blind_token("tariff_single_device", self.mock_config["token_secret"])
        
        self.central_db[token_json] = {
            "is_active": True,
            "expiry": time.time() + 3600,
            "max_devices": 1,
            "active_devices": 0,
            "registered_devices": []
        }
        
        manager = access_manager.AccessManager(self.central_db, self.mock_config["token_secret"])
        
        res1 = manager.check_access(token_json, device_id="device_A")
        self.assertTrue(res1["allowed"])
        self.assertEqual(self.central_db[token_json]["active_devices"], 1)
        
        res2 = manager.check_access(token_json, device_id="device_B")
        self.assertFalse(res2["allowed"])
        self.assertIn("fraud", res2.get("reason", "").lower())

if __name__ == '__main__':
    unittest.main()