import os
import sys
import json
import time
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

class TestDistributedRegistry(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.base_dir, '..', 'config', 'registry_config.json')
        self.mock_config = {
            "gossip_interval_seconds": 0.1,
            "max_hops": 5,
            "network_key_public": "mock_pub_key_node_a",
            "network_key_private": "mock_priv_key_node_a"
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.mock_config, f)
            
        # Импортируем модули после настройки путей
        import registry_crypto
        import gossip_protocol
        
        self.crypto = registry_crypto.RegistryCrypto(self.config_path)
        self.node_a = gossip_protocol.GossipNode("node_a", self.config_path, self.crypto)
        self.node_b = gossip_protocol.GossipNode("node_b", self.config_path, self.crypto)
        self.node_c = gossip_protocol.GossipNode("node_c", self.config_path, self.crypto)

    def test_01_avalanche_delivery(self):
        """Тест 1: Лавинообразная доставка (цель < 5 секунд)"""
        import gossip_protocol

        # Узел А получает новое состояние (например, новый шлюз)
        new_state = {
            "type": "gateway_update",
            "gateway_id": "gw_new_123",
            "status": "active",
            "timestamp": time.time(),
            "data": {"ip": "10.0.0.5"}
        }
        
        # Подписываем и добавляем в узел А
        signed_update = self.node_a.create_signed_update(new_state)
        self.node_a.apply_update(signed_update, "node_a")

        # Симуляция лавинообразной рассылки: A -> B, затем B -> C
        start_time = time.time()

        # A синхронизируется с B
        updates_from_a = self.node_a.get_pending_updates()
        for upd in updates_from_a:
            res_b = self.node_b.receive_update(upd)
            self.assertTrue(res_b["success"], f"Node B failed to receive update: {res_b}")

        # B синхронизируется с C
        updates_from_b = self.node_b.get_pending_updates()
        self.assertGreater(len(updates_from_b), 0, "Node B has no pending updates to forward")
        for upd in updates_from_b:
            res_c = self.node_c.receive_update(upd)
            self.assertTrue(res_c["success"], f"Node C failed to receive update: {res_c}")
            
        elapsed = time.time() - start_time
        
        # Проверяем, что все узлы получили состояние
        self.assertIn("gw_new_123", self.node_a.state["gateways"])
        self.assertIn("gw_new_123", self.node_b.state["gateways"])
        self.assertIn("gw_new_123", self.node_c.state["gateways"])
        
        # Проверяем время доставки (должно быть < 5 секунд)
        self.assertLess(elapsed, 5.0, "Доставка обновления заняла слишком много времени")

    def test_02_forgery_rejection(self):
        """Тест 2: Отсечение поддельных команд и блокировка атакующего"""
        import registry_crypto
        import gossip_protocol

        # Атакующий создает обновление, но мы намеренно портим подпись, 
        # чтобы симулировать использование невалидного/чужого ключа
        malicious_update = {
            "type": "node_ban",
            "target_node": "node_b",
            "timestamp": time.time(),
            "data": {"reason": "fake ban"}
        }
        
        # Атакующий подписывает своими ключами
        attacker_crypto = registry_crypto.RegistryCrypto(self.config_path)
        attacker_node = gossip_protocol.GossipNode("attacker", self.config_path, attacker_crypto)
        signed_malicious = attacker_node.create_signed_update(malicious_update)
        
        # Намеренно повреждаем подпись (валидный hex, но неверная криптографическая подпись), 
        # чтобы проверка узла B гарантированно провалилась
        signed_malicious["signature"] = "00" * 64

        # Узел B получает поддельное сообщение
        initial_blacklist_len = len(self.node_b.blacklist)
        result = self.node_b.receive_update(signed_malicious)
        
        # Ожидаем отказ и добавление в черный список
        self.assertFalse(result["success"])
        self.assertIn("invalid_signature", result["reason"].lower())
        self.assertEqual(len(self.node_b.blacklist), initial_blacklist_len + 1)
        self.assertIn("attacker", self.node_b.blacklist)

    def test_03_master_node_down_resilience(self):
        """Тест 3: Работа при выключенном Центре (P2P синхронизация и валидация)"""
        import gossip_protocol

        # Мастер-нода (node_m) отсутствует в сети. Есть только frontend (node_a) и backend (node_b).
        # Они должны синхронизировать отозванные токены и состояния шлюзов автономно.

        # 1. Узел А добавляет отозванный токен в свой реестр
        revoked_token_update = {
            "type": "token_revoke",
            "token_id": "revoked_token_999",
            "timestamp": time.time(),
            "data": {"reason": "payment_failed"}
        }
        signed_revoke = self.node_a.create_signed_update(revoked_token_update)
        self.node_a.apply_update(signed_revoke, "node_a")

        # 2. Узел А синхронизируется с Узлом Б
        updates = self.node_a.get_pending_updates()
        for upd in updates:
            self.node_b.receive_update(upd)

        # 3. Проверяем, что Узел Б знает об отозванном токене
        self.assertIn("revoked_token_999", self.node_b.state["revoked_tokens"])

        # 4. Проверяем, что при попытке использования этого токена доступ будет закрыт
        is_revoked = self.node_b.is_token_revoked("revoked_token_999")
        self.assertTrue(is_revoked)

if __name__ == '__main__':
    unittest.main()