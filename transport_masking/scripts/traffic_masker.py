#!/usr/bin/env python3
"""
Алгоритм идеальной маскировки трафика SafeNet service.
Реализует имитацию легитимного HTTPS-трафика, скоростной фоллбек и динамическую смену SNI.
"""
import json
import os
import random

# Порог нагрузки для переключения на скоростной режим (в Мбит/с или %)
SPEED_THRESHOLD = 80.0

class TrafficMasker:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.current_target = self.config.get('current_target', 'www.amazon.com')
        self.mode = 'stealth' # 'stealth' или 'high_speed_mode'

    def get_current_headers(self) -> dict:
        """Возвращает подмененные заголовки для имитации целевого сайта."""
        for target in self.config['targets']:
            if target['domain'] == self.current_target:
                return target['headers']
        # Fallback заголовки, если цель не найдена
        return {
            "Server": "nginx/1.22.0",
            "Content-Type": "text/html; charset=utf-8"
        }

    def evaluate_packet_for_dpi(self, packet_payload: bytes) -> bool:
        """
        Тест 1: Имитация проверки DPI.
        Проверяет, что пакет не содержит service-сигнатур и выглядит как TLS 1.3 Application Data или Handshake.
        """
        no_vpn_signatures = True
        # Проверяем отсутствие сигнатур популярных service-протоколов в полезной нагрузке
        vpn_keywords = [b'wireguard', b'openvpn', b'x-custom-service', b'x-custom-wg']
        for kw in vpn_keywords:
            if kw in packet_payload.lower():
                no_vpn_signatures = False
                break
        
        # Имитация TLS Handshake (Client Hello начинается с 0x16 0x03 0x01)
        is_tls_like = packet_payload.startswith(b'\x16\x03\x01') or packet_payload.startswith(b'\x17\x03\x03')
        
        return is_tls_like and no_vpn_signatures

    def evaluate_speed_switch(self, current_load: float, content_type: str) -> str:
        """
        Тест 2: Автоматическое переключение на скорость.
        Если нагрузка высокая или запрашивается потоковое видео/стриминг, переключаемся на high_speed_mode.
        """
        if current_load > SPEED_THRESHOLD or 'video' in content_type.lower() or 'stream' in content_type.lower():
            self.mode = 'high_speed_mode'
            return 'high_speed_mode'
        else:
            self.mode = 'stealth'
            return 'stealth'

    def rotate_camouflage_target(self) -> str:
        """Динамическая смена маскировочного адреса (SNI)."""
        domains = [t['domain'] for t in self.config['targets']]
        # Выбираем новую цель, отличную от текущей
        available = [d for d in domains if d != self.current_target]
        if available:
            self.current_target = random.choice(available)
            self.config['current_target'] = self.current_target
            return self.current_target
        return self.current_target

if __name__ == "__main__":
    # Демонстрация работы
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'camouflage_targets.json')
    masker = TrafficMasker(config_path)
    
    print(f"[INFO] Текущая цель маскировки: {masker.current_target}")
    print(f"[INFO] Заголовки для подмены: {masker.get_current_headers()}")
    
    # Тест DPI
    fake_tls_packet = b'\x16\x03\x01\x00\x00' # Client Hello
    is_safe = masker.evaluate_packet_for_dpi(fake_tls_packet)
    print(f"[DPI CHECK] Пакет распознан как легитимный TLS: {is_safe}")
    
    # Тест переключения скорости
    new_mode = masker.evaluate_speed_switch(current_load=85.0, content_type='video/mp4')
    print(f"[MODE SWITCH] Активирован режим: {new_mode}")