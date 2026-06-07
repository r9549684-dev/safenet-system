import os
import re
import unittest

class TestMasterNodeIsolation(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.script_path = os.path.join(base_dir, '..', 'scripts', 'deploy_master.sh')
        self.knockd_path = os.path.join(base_dir, '..', 'config', 'knockd.conf')
        
    def test_01_deployment_cleanliness(self):
        """Тест 3: Чистота развертывания - скрипт не требует ручного ввода и содержит базовую защиту"""
        with open(self.script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('DEBIAN_FRONTEND=noninteractive', content, "Скрипт должен использовать noninteractive режим")
        self.assertIn('apt-get install -y', content, "Установка пакетов должна быть автоматической (-y)")
        self.assertIn('iptables', content, "Скрипт должен настраивать iptables")
        self.assertIn('DROP', content, "Политика по умолчанию должна быть DROP")
        self.assertIn('knockd', content, "Должен быть установлен и настроен port knocking")

    def test_02_anti_scan_camouflage(self):
        """Тест 1: Имитация атаки - проверка правил скрытия от сканеров"""
        with open(self.script_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.assertTrue(
            re.search(r'iptables.*-p\s+icmp.*--icmp-type\s+echo-request.*-j\s+DROP', content) or
            re.search(r'iptables.*-A\s+INPUT.*-p\s+icmp.*-j\s+DROP', content),
            "Скрипт должен блокировать ICMP echo-request (ping)"
        )
        self.assertIn('iptables -P INPUT DROP', content, "Входящий трафик по умолчанию должен сбрасываться")
        self.assertIn('iptables -P FORWARD DROP', content, "Форвардинг по умолчанию должен быть запрещен")

    def test_03_trusted_channel_logic(self):
        """Тест 2: Доверенный канал - проверка логики port knocking"""
        with open(self.knockd_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.assertIn('sequence', content, "Должна быть задана последовательность портов для knock")
        self.assertIn('tcpflags', content, "Должны проверяться TCP-флаги (syn)")
        self.assertIn('cmd_timeout', content, "Должно быть ограничение времени действия правила")
        self.assertIn('start_command', content, "Должна быть команда для открытия порта")
        self.assertIn('stop_command', content, "Должна быть команда для закрытия порта после таймаута")

if __name__ == '__main__':
    unittest.main()
