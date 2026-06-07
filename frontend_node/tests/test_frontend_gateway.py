import os
import re
import unittest
import time

class TestFrontendGateway(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.deploy_script = os.path.join(self.base_dir, '..', 'scripts', 'deploy_frontend.sh')
        self.rotate_script = os.path.join(self.base_dir, '..', 'scripts', 'rotate_gateway.sh')
        
    def test_01_rotation_speed_logic(self):
        """Тест 1: Скорость ротации - проверка наличия логики быстрого пересоздания"""
        with open(self.rotate_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем, что скрипт содержит этапы: уничтожение, создание, ожидание готовности
        self.assertIn('destroy', content.lower(), "Скрипт должен содержать команду уничтожения старого шлюза")
        self.assertIn('create', content.lower(), "Скрипт должен содержать команду создания нового шлюза")
        self.assertIn('timeout', content.lower(), "Должен быть задан таймаут ожидания готовности (до 3 минут)")
        self.assertLess(len(content.split('\n')), 50, "Скрипт ротации должен быть минималистичным и быстрым")

    def test_02_no_digital_footprint(self):
        """Тест 2: Отсутствие цифрового следа - проверка отключения логирования"""
        with open(self.deploy_script, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Проверяем очистку или перенаправление логов в RAM (tmpfs)
        self.assertTrue(
            re.search(r'tmpfs\s+/var/log\s+tmpfs', content) or
            re.search(r'rm\s+-rf\s+/var/log/.*', content),
            "Логи должны быть отключены или перенесены в оперативную память (tmpfs)"
        )
        self.assertIn('history -c', content, "История команд должна очищаться")
        self.assertIn('rsyslog', content.lower(), "Демон системного логирования должен быть остановлен/удален")
        self.assertIn('noatime', content.lower(), "Файловая система должна монтироваться без обновления времени доступа")

    def test_03_auto_sync_with_center(self):
        """Тест 3: Автоматическая синхронизация - проверка связи с Центром"""
        with open(self.rotate_script, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Проверяем Port Knocking перед отправкой данных
        self.assertTrue(
            re.search(r'knock\s+\S+\s+7000\s+8000\s+9000', content),
            "Перед синхронизацией должен выполняться Port Knocking по секретной последовательности"
        )
        # Проверяем отправку IP-адреса на центр
        self.assertTrue(
            re.search(r'curl.*http.*\$MASTER_IP.*register.*ip', content, re.IGNORECASE | re.DOTALL),
            "Скрипт должен отправлять свой новый IP-адрес на Управляющий узел после поднятия"
        )

if __name__ == '__main__':
    unittest.main()