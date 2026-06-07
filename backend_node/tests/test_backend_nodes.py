import os
import re
import unittest

class TestBackendNodes(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.deploy_script = os.path.join(self.base_dir, '..', 'scripts', 'deploy_backend.sh')
        self.balancer_script = os.path.join(self.base_dir, '..', 'scripts', 'backend_balancer.py')
        
    def test_01_isolation_check(self):
        """Тест 1: Проверка изоляции - Backend принимает трафик только от доверенных Frontend IP"""
        with open(self.deploy_script, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Проверка строгой политики DROP
        self.assertIn('iptables -P INPUT DROP', content, "Политика ввода по умолчанию должна быть DROP")
        self.assertIn('iptables -P FORWARD DROP', content, "Форвардинг по умолчанию должен быть запрещен")
        
        # Проверка наличия правила, разрешающего трафик только с конкретных IP (имитация frontend)
        self.assertTrue(
            re.search(r'iptables.*-s.*FRONTEND.*-p\s+(udp|tcp).*--dport.*-j\s+ACCEPT', content, re.IGNORECASE),
            "Должно быть правило, разрешающее входящий трафик только с доверенных IP-адресов"
        )
        self.assertIn('wg-quick', content.lower(), "Для туннелирования должен использоваться WireGuard или аналог")

    def test_02_tunnel_integrity(self):
        """Тест 2: Пропускной канал - проверка конфигурации защищенного туннеля и отсутствия логов"""
        with open(self.deploy_script, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Проверка отключения логов WireGuard (или перенаправления)
        self.assertTrue(
            re.search(r'tmpfs\s+/var/log\s+tmpfs', content) or
            re.search(r'rm\s+-rf\s+/var/log/\*', content),
            "Логи на Backend-ноде должны быть отключены или находиться в RAM"
        )
        # Проверка инкапсуляции (WireGuard сохраняет конфиденциальность)
        self.assertIn('AllowedIPs', content, "WireGuard должен использовать строгие AllowedIPs для изоляции трафика")

    def test_03_auto_balancing_logic(self):
        """Тест 3: Автоматическая балансировка - проверка алгоритма оценки нагрузки"""
        with open(self.balancer_script, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Проверка сбора метрик загрузки (CPU или Load Average)
        self.assertTrue(
            re.search(r'loadavg|cpu_percent|uptime', content, re.IGNORECASE),
            "Балансировщик должен опрашивать метрики загрузки сервера (CPU/Load)"
        )
        # Проверка логики переключения при перегрузке
        self.assertTrue(
            re.search(r'if.*load.*>\s*\d+|threshold|overload', content, re.IGNORECASE),
            "Должен быть порог перегрузки, при котором трафик перенаправляется на резервный узел"
        )
        self.assertIn('register', content.lower(), "Балансировщик должен сообщать о своем статусе диспетчеру")

if __name__ == '__main__':
    unittest.main()