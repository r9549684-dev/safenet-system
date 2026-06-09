import os
import re
import json
import unittest

class TestTransportMasking(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.masker_script = os.path.join(self.base_dir, '..', 'scripts', 'traffic_masker.py')
        self.config_file = os.path.join(self.base_dir, '..', 'config', 'camouflage_targets.json')
        self.rotate_script = os.path.join(self.base_dir, '..', 'scripts', 'rotate_camouflage.sh')

    def test_01_dpi_imitation(self):
        """Тест 1: Имитация проверки DPI - трафик должен выглядеть как обычный HTTPS, без признаков service"""
        with open(self.masker_script, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Проверяем наличие логики формирования TLS 1.3 Handshake с подменой SNI
        self.assertTrue(
            re.search(r'tls|sni|handshake|application_data', content, re.IGNORECASE),
            "Должна быть реализация имитации TLS-рукопожатия и SNI"
        )
        # Проверяем отсутствие или блокировку service-сигнатур (WireGuard, OpenVPN)
        self.assertTrue(
            re.search(r'block.*wireguard|drop.*openvpn|no_vpn_signatures', content, re.IGNORECASE),
            "Скрипт должен явно блокировать или не использовать service-сигнатуры в исходящем трафике"
        )

    def test_02_auto_speed_switch(self):
        """Тест 2: Автоматическое переключение на скорость - реакция на нагрузку или тип контента"""
        with open(self.masker_script, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Проверяем триггеры для переключения: высокая нагрузка или видео/стриминг
        self.assertTrue(
            re.search(r'load.*threshold|video|stream|bandwidth.*>.*\d+', content, re.IGNORECASE),
            "Должны быть условия для переключения на скоростной режим (нагрузка или тип контента)"
        )
        self.assertIn('high_speed_mode', content.lower(), "Должен быть активен режим 'high_speed_mode' или аналог")

    def test_03_header_spoofing_correctness(self):
        """Тест 3: Корректность подмены заголовков - ответы сервера должны быть чистыми"""
        with open(self.masker_script, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Проверяем наличие стандартных заголовков легитимного сайта (в формате словаря Python или JSON)
        self.assertTrue(
            re.search(r'"Server":\s*"nginx|"Server":\s*"Server', content, re.IGNORECASE),
            "Должен подставляться легитимный заголовок Server"
        )
        self.assertTrue(
            re.search(r'"Content-Type":\s*"text/html|"Content-Type":\s*"application/json', content, re.IGNORECASE),
            "Должен быть корректный Content-Type"
        )
        # Проверяем, что service-заголовки явно отсутствуют или удаляются (проверка как ключей словаря или значений)
        self.assertFalse(
            re.search(r'["\']x-service["\']|["\']x-wireguard["\']', content, re.IGNORECASE),
            "В подменяемых заголовках не должно быть упоминаний service"
        )

    def test_04_dynamic_camouflage_config(self):
        """Доп. проверка: Наличие конфигурации для динамической смены маскировочных адресов"""
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        self.assertIn('targets', config, "Конфиг должен содержать список целей для маскировки")
        self.assertGreaterEqual(len(config['targets']), 2, "Должно быть минимум 2 цели для ротации")
        self.assertIn('current_target', config, "Должен быть указан текущий цели маскировки")

if __name__ == '__main__':
    unittest.main()