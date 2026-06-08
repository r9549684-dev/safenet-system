import json
import os
import time
from typing import List, Optional

class FelixDispatcher:
    def __init__(self, config_path: str, state_path: str):
        self.config_path = config_path
        self.state_path = state_path
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        with open(state_path, 'r', encoding='utf-8') as f:
            self.state = json.load(f)
            
        self.auto_retry_count = 0
        self.max_auto_retries = self.config.get("max_auto_retries", 3)

    def _save_state(self):
        with open(self.state_path, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2)

    def record_failure(self, region: str):
        """Логика 'Умного Контекста': запись сбоя региона."""
        if region not in self.state.get("failed_regions", []):
            if "failed_regions" not in self.state:
                self.state["failed_regions"] = []
            self.state["failed_regions"].append(region)
            self._save_state()

    def select_safe_region(self, available_regions: List[str]) -> Optional[str]:
        """Выбор региона, исключая те, что часто блокируются."""
        blacklisted = set(self.config.get("blacklisted_regions", []))
        blacklisted.update(self.state.get("failed_regions", []))
        
        for region in available_regions:
            if region not in blacklisted:
                return region
        return available_regions[0] if available_regions else None

    def destroy_instance(self, gateway_id: str):
        """Удаление старого шлюза на хостинге."""
        print(f"[FELIX] Уничтожение скомпрометированного шлюза: {gateway_id}")
        # Здесь был бы вызов API хостинга
        time.sleep(0.1) # Имитация задержки сети

    def provision_instance(self, region: str) -> str:
        """Аренда нового шлюза и накат конфигурации Zero Footprint."""
        print(f"[FELIX] Аренда нового шлюза в регионе: {region}")
        # Здесь вызов API хостинга, который может упасть с 503
        if region == "eu-west-2":  # Эмуляция сбоя для теста
            raise Exception("Cloud API 503 Service Unavailable")
        return f"gw-new-{int(time.time())}"

    def port_knock_center(self, new_ip: str):
        """Проведение Port Knocking в Центр для открытия доверенного канала."""
        print(f"[FELIX] Port Knocking в Центр для IP: {new_ip}")
        # Здесь逻辑 стучания в master_ip

    def update_dns_record(self, new_gateway_info: dict):
        """Обновление зашифрованной DNS-записи."""
        print(f"[FELIX] Обновление DNS-записи с новыми данными шлюза")
        # Вызов dns_updater.update_dns_record

    def notify_user(self, message: str):
        """Отправка структурированного запроса пользователю (ТОЛЬКО при критических тупиках)."""
        print(f"[FELIX -> USER] {message}")

    def handle_network_error(self, error_msg: str):
        """Обработка штатных сетевых ошибок БЕЗ тревожных уведомлений пользователю."""
        standard_errors = ["timeout", "failed", "glitch", "502", "503", "504"]
        if any(err in error_msg.lower() for err in standard_errors):
            print(f"[FELIX] Штатная сетевая ошибка подавлена (автономное решение): {error_msg}")
            return
        print(f"[FELIX] Нестандартная ошибка: {error_msg}")

    def handle_gateway_drop(self, gateway_id: str):
        """
        Замкнутый JIT-цикл самодиагностики и автозамены.
        Если задача принципиально неразрешима автоматически (критический тупик), 
        собирает диагностику и запрашивает помощь у пользователя.
        """
        print(f"[FELIX] Обнаружено падение шлюза: {gateway_id}. Запуск JIT-цикла...")
        
        try:
            # 1. Удалить старый шлюз
            self.destroy_instance(gateway_id)
            
            # 2. Выбрать безопасный регион
            safe_region = self.select_safe_region(["eu-west-2", "us-east-1"])
            if not safe_region:
                raise Exception("Нет доступных безопасных регионов для развертывания")
                
            # 3. Арендовать новый и накатить конфиг (может выбросить исключение при крахе API)
            new_gateway_id = self.provision_instance(safe_region)
            new_ip = "203.0.113.100" # Получается из API провайдера
            
            # 4. Связать с Центром (Port Knocking)
            self.port_knock_center(new_ip)
            
            # 5. Обновить DNS-запись
            self.update_dns_record({"gateway_id": new_gateway_id, "ip": new_ip})
            
            print("[FELIX] JIT-цикл успешно завершен. Сетевая целостность восстановлена.")
            self.auto_retry_count = 0 # Сброс счетчика при успехе
            
        except Exception as critical_error:
            self.auto_retry_count += 1
            print(f"[FELIX] Критическая ошибка в JIT-цикле (попытка {self.auto_retry_count}/{self.max_auto_retries}): {critical_error}")
            
            if self.auto_retry_count >= self.max_auto_retries:
                # КРИТИЧЕСКИЙ ТУПИК: Автоматически решить невозможно
                report = (
                    "⚠️ КРИТИЧЕСКИЙ СБОЙ: Автономное восстановление сети невозможно.\n"
                    f"Причина: {str(critical_error)}\n\n"
                    "ВАРИАНТЫ РЕШЕНИЯ:\n"
                    "1. Проверить баланс и квоты в панели облачного хостинга.\n"
                    "2. Временно сменить основного провайдера хостинга в конфигурации.\n"
                    "3. Подтвердить ручное развертывание резервного узла.\n\n"
                    "Ожидаю вашей команды. Все штатные попытки приостановлены."
                )
                self.notify_user(report)