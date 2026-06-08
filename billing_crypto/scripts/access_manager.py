import time
import blind_tokens

class AccessManager:
    def __init__(self, central_db: dict, secret: str):
        self.central_db = central_db
        self.secret = secret

    def check_access(self, token_json_str: str, device_id: str) -> dict:
        """
        Проверяет доступ для устройства по токену.
        Возвращает словарь с флагом 'allowed' и причиной/редиректом при отказе.
        """
        # 1. Stateless криптографическая проверка (валидность подписи и срока в самом токене)
        is_valid, payload = blind_tokens.validate_token(token_json_str, self.secret)
        if not is_valid:
            if payload.get("error") == "Token expired":
                return {
                    "allowed": False,
                    "reason": "Token expired",
                    "redirect_to": "dns_payment_channel"
                }
            return {"allowed": False, "reason": "Invalid token"}

        # 2. Проверка состояния в Central DB (защита от отзыва, контроль устройств)
        if token_json_str not in self.central_db:
            return {"allowed": False, "reason": "Token not found in DB"}
            
        record = self.central_db[token_json_str]
        
        if not record.get("is_active"):
            return {"allowed": False, "reason": "Account deactivated", "redirect_to": "dns_payment_channel"}
            
        if time.time() > record.get("expiry", 0):
            record["is_active"] = False
            return {
                "allowed": False,
                "reason": "Subscription expired",
                "redirect_to": "dns_payment_channel"
            }
            
        # 3. Контроль одновременных подключений (Anti-Fraud)
        max_devices = record.get("max_devices", 1)
        registered_devices = record.get("registered_devices", [])
        
        if device_id in registered_devices:
            return {"allowed": True, "reason": "Known device"}
            
        if len(registered_devices) >= max_devices:
            return {
                "allowed": False,
                "reason": "fraud: max devices exceeded",
                "redirect_to": "upgrade_tariff"
            }
            
        # Регистрация нового устройства
        registered_devices.append(device_id)
        record["active_devices"] = len(registered_devices)
        record["registered_devices"] = registered_devices
        
        return {"allowed": True, "reason": "Access granted"}