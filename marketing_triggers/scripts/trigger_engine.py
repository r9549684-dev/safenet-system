import json
import os
from typing import Optional, Dict, Any

class TriggerEngine:
    def __init__(self, config_path: str):
        self.config_path = config_path
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def evaluate_technical_state(self, user_id: str, current_speed_mbps: float) -> Optional[str]:
        """Оценивает техническое состояние и генерирует триггер при падении скорости."""
        threshold = self.config.get("bandwidth_threshold_mbps", 5.0)
        if current_speed_mbps < threshold:
            return (
                f"Заметили, что у вас проседает скорость? 📉 "
                f"Мы уже открыли для вас выделенный скоростной шлюз. "
                f"Нажмите 'Подключить', чтобы переключиться мгновенно!"
            )
        return None

    def evaluate_commercial_state(self, user_id: str, days_left: int, traffic_used_percent: float) -> Optional[str]:
        """Оценивает коммерческое состояние (подписка, трафик)."""
        days_threshold = self.config.get("days_before_expiry_alert", 3)
        if days_left <= days_threshold:
            return (
                f"⏳ Ваша подписка истекает через {days_left} дн. "
                f"Не теряйте защиту! Продлите сейчас и получите скидку 20% по промокоду STAY20."
            )
        if traffic_used_percent > 90.0:
            return (
                f"📊 Вы израсходовали {int(traffic_used_percent)}% трафика. "
                f"Чтобы не остаться без связи, рекомендуем увеличить лимит в один клик."
            )
        return None

    def evaluate_marketing_state(self, user_id: str, active_devices: int) -> Optional[str]:
        """Оценивает маркетинговые возможности (например, апсейл)."""
        if active_devices == 1:
            offer = self.config.get("marketing_offers", {}).get("single_device", "")
            if offer:
                return f"🚀 {offer} Активируйте в настройках за 10 секунд!"
        return None

    def process_user_state(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Комплексная оценка состояния пользователя. Возвращает самое приоритетное сообщение."""
        # 1. Технический триггер имеет высший приоритет (проблема с сервисом)
        tech_msg = self.evaluate_technical_state(user_data["id"], user_data.get("speed_mbps", 100.0))
        if tech_msg:
            return tech_msg
            
        # 2. Коммерческий триггер (деньги)
        comm_msg = self.evaluate_commercial_state(
            user_data["id"], 
            user_data.get("days_left", 30), 
            user_data.get("traffic_used_percent", 0.0)
        )
        if comm_msg:
            return comm_msg
            
        # 3. Маркетинговый триггер (рост)
        mkt_msg = self.evaluate_marketing_state(user_data["id"], user_data.get("active_devices", 0))
        return mkt_msg