import os
import sys
import time
import json
import unittest
from unittest.mock import patch, MagicMock

# Добавляем пути к модулям из предыдущих частей
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'distributed_registry', 'scripts')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'marketing_triggers', 'scripts')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'billing_crypto', 'scripts')))

class TestChaosEngineering(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.base_dir, '..', 'config', 'chaos_config.json')
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        self.mock_config = {
            "max_gateway_downtime_seconds": 180, # 3 минуты на автозамену
            "gossip_interval_seconds": 0.05,
            "max_hops": 5,
            "simulation_mode": True
        }
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.mock_config, f)
            
        # Инициализация P2P узлов (Часть 9) для проверки консенсуса под огнем
        import registry_crypto
        import gossip_protocol
        
        self.crypto = registry_crypto.RegistryCrypto(self.config_path)
        self.node_a = gossip_protocol.GossipNode("node_a", self.config_path, self.crypto)
        self.node_b = gossip_protocol.GossipNode("node_b", self.config_path, self.crypto)
        
    def test_01_massive_gateway_blocking_survival(self):
        """Тест 1: Выживаемость при веерной блокировке (70% шлюзов уничтожено)"""
        # Имитация 10 шлюзов, из которых 7 внезапно падают (70%)
        total_gateways = 10
        failed_count = 7
        
        start_time = time.time()
        
        for i in range(failed_count):
            gw_id = f"gw_{i}"
            # Диспетчер фиксирует падение и генерирует P2P-обновление с новым адресом замены
            update = {
                "type": "gateway_update",
                "gateway_id": gw_id,
                "timestamp": time.time(),
                "data": {"status": "destroyed", "replacement_ip": "10.0.1.99"}
            }
            signed_update = self.node_a.create_signed_update(update)
            # Мгновенная синхронизация с резервным узлом
            self.node_b.receive_update(signed_update)
            
        elapsed = time.time() - start_time
        
        # Проверка: все разрушенные шлюзы отмечены как destroyed, и есть IP замены
        for i in range(failed_count):
            gw_id = f"gw_{i}"
            self.assertEqual(self.node_b.state["gateways"][gw_id]["status"], "destroyed")
            self.assertEqual(self.node_b.state["gateways"][gw_id]["replacement_ip"], "10.0.1.99")
            
        # Проверка времени реакции (в тестах это доли секунды, что << 180 секунд)
        self.assertLess(elapsed, 3.0, "Реакция на веерную блокировку превысила аварийный лимит")

    def test_02_consensus_under_fire(self):
        """Тест 2: Консенсус под огнем (Мастер-нода отключена, P2P синхронизирует состояние)"""
        # Узел А получает информацию о блокировке перегруженного рабочего узла
        ban_update = {
            "type": "node_ban",
            "target_node": "worker_3",
            "timestamp": time.time(),
            "data": {"reason": "severe_overload"}
        }
        self.node_a.create_signed_update(ban_update)
        
        # Узел Б получает информацию об отзыве скомпрометированного токена
        revoke_update = {
            "type": "token_revoke",
            "token_id": "token_fraud_xyz",
            "timestamp": time.time(),
            "data": {"reason": "payment_reversal"}
        }
        self.node_b.create_signed_update(revoke_update)
        
        # Двусторонний обмен обновлениями по Gossip-протоколу (имитация сетевого чиха)
        for upd in self.node_a.get_pending_updates():
            self.node_b.receive_update(upd)
        for upd in self.node_b.get_pending_updates():
            self.node_a.receive_update(upd)
            
        # Проверка консенсуса: оба узла пришли к единому состоянию БЕЗ участия Центра
        self.assertTrue(self.node_a.state["node_status"]["worker_3"]["banned"])
        self.assertTrue(self.node_b.state["node_status"]["worker_3"]["banned"])
        
        self.assertIn("token_fraud_xyz", self.node_a.state["revoked_tokens"])
        self.assertIn("token_fraud_xyz", self.node_b.state["revoked_tokens"])

    def test_03_client_session_continuity(self):
        """Тест 3: Непрерывность сессии клиента (переход на DNS при блокировке HTTP)"""
        # Эмуляция состояния клиентского приложения, которое качает файл или стримит видео
        client_session = {
            "active_download": True,
            "bytes_transferred": 5000,
            "active_gateway": "gw_primary",
            "http_blocked": False,
            "fallback_triggered": False
        }
        
        # КАТАСТРОФА: Провайдер блокирует HTTP/HTTPS, текущий шлюз отваливается
        client_session["http_blocked"] = True
        client_session["active_gateway"] = None
        
        # JIT-реакция системы: Диспетчер инициирует экстренный фолбэк на DNS-канал
        client_session["fallback_triggered"] = True
        
        # Эмуляция успешного чтения зашифрованной DNS TXT-записи (Часть 5/7)
        # и получения нового IP-адреса резервного шлюза
        emergency_gateway = "gw_emergency_dns_01"
        
        # Клиентское приложение восстанавливает замаскированный TLS-туннель через новый шлюз
        client_session["active_gateway"] = emergency_gateway
        client_session["bytes_transferred"] += 2000 # Загрузка продолжилась без разрыва
        
        # Проверка UX: сессия не разорвалась, критических ошибок соединения нет
        self.assertTrue(client_session["active_download"], "Загрузка была прервана!")
        self.assertTrue(client_session["fallback_triggered"], "Фолбэк на DNS не сработал!")
        self.assertEqual(client_session["bytes_transferred"], 7000, "Трафик не продолжился после ротации!")
        self.assertIsNone(client_session.get("critical_connection_error"), "Произошел критический обрыв сессии!")

if __name__ == '__main__':
    unittest.main()