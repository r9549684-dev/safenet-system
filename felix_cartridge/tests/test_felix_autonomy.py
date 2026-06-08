import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

class TestFelixAutonomy(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.base_dir, '..', 'config', 'felix_config.json')
        self.state_path = os.path.join(self.base_dir, '..', 'config', 'state_journal.json')
        
        self.mock_config = {
            "master_ip": "10.0.0.1",
            "cloud_api_token": "mock_token",
            "blacklisted_regions": ["eu-west-2"],
            "max_auto_retries": 3
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.mock_config, f)
            
        with open(self.state_path, 'w', encoding='utf-8') as f:
            json.dump({"failed_regions": []}, f)

    def test_01_emulate_drop_and_auto_replace(self):
        """Тест 1: Эмуляция падения и автозамена шлюза без уведомления пользователя"""
        import felix_dispatcher
        
        dispatcher = felix_dispatcher.FelixDispatcher(self.config_path, self.state_path)
        
        with patch.object(dispatcher, 'destroy_instance') as mock_destroy, \
             patch.object(dispatcher, 'provision_instance') as mock_provision, \
             patch.object(dispatcher, 'port_knock_center') as mock_knock, \
             patch.object(dispatcher, 'update_dns_record') as mock_dns, \
             patch.object(dispatcher, 'notify_user') as mock_notify:
            
            # Эмуляция падения шлюза
            dispatcher.handle_gateway_drop("gw-old-123")
            
            # Проверяем полный цикл JIT-администрирования
            mock_destroy.assert_called_once_with("gw-old-123")
            mock_provision.assert_called_once()
            mock_knock.assert_called_once()
            mock_dns.assert_called_once()
            
            # КРИТИЧЕСКИ ВАЖНО: Пользователь НЕ должен быть уведомлен о штатном сбое
            mock_notify.assert_not_called()

    def test_02_no_distraction_for_standard_errors(self):
        """Тест 2: Ограничение на отвлекающие факторы - штатные ошибки не шлют уведомления"""
        import felix_dispatcher
        
        dispatcher = felix_dispatcher.FelixDispatcher(self.config_path, self.state_path)
        
        standard_errors = [
            "Connection timeout",
            "DNS resolution failed",
            "Temporary network glitch",
            "502 Bad Gateway"
        ]
        
        with patch.object(dispatcher, 'notify_user') as mock_notify:
            for err in standard_errors:
                dispatcher.handle_network_error(err)
                
            # Ни одно штатное уведомление не должно дойти до пользователя
            self.assertEqual(mock_notify.call_count, 0)

    def test_03_request_help_in_critical_deadlock(self):
        """Тест 3: Запрос помощи при критическом тупике (API хостинга недоступен)"""
        import felix_dispatcher
        
        dispatcher = felix_dispatcher.FelixDispatcher(self.config_path, self.state_path)
        dispatcher.max_auto_retries = 1 # Ускоряем наступление критического тупика в тесте
        
        # Эмуляция полного краха API облачного хостинга
        with patch.object(dispatcher, 'provision_instance') as mock_provision:
            mock_provision.side_effect = Exception("Cloud API 503 Service Unavailable")
            
            with patch.object(dispatcher, 'notify_user') as mock_notify:
                dispatcher.handle_gateway_drop("gw-critical-999")
                
                # Проверяем, что после исчерпания попыток был вызван notify_user
                self.assertTrue(mock_notify.called)
                
                # Проверяем структуру запроса о помощи
                call_args = mock_notify.call_args[0][0]
                self.assertIn("КРИТИЧЕСКИЙ СБОЙ", call_args)
                self.assertIn("ВАРИАНТЫ РЕШЕНИЯ", call_args)
                self.assertIn("1. Проверить баланс", call_args)
                self.assertIn("2. Временно сменить основного провайдера", call_args)

    def test_04_smart_context_blacklisting(self):
        """Доп. проверка: Логика 'Умного Контекста' - избегание проблемных регионов"""
        import felix_dispatcher
        
        dispatcher = felix_dispatcher.FelixDispatcher(self.config_path, self.state_path)
        
        # Симулируем 3 сбоя в одном регионе
        for _ in range(3):
            dispatcher.record_failure("eu-west-2")
            
        # Проверяем, что регион добавлен в черный список
        with open(self.state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
            
        self.assertIn("eu-west-2", state["failed_regions"])
        
        # Проверяем, что при выборе региона он будет исключен
        chosen_region = dispatcher.select_safe_region(["eu-west-2", "us-east-1"])
        self.assertEqual(chosen_region, "us-east-1")

if __name__ == '__main__':
    unittest.main()