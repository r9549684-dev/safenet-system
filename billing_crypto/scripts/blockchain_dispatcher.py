import time
import json
import secrets
import blind_tokens

class BlockchainDispatcher:
    def __init__(self, config_path: str, central_db: dict):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.central_db = central_db

    def generate_payment_address(self) -> str:
        """Генерирует уникальный одноразовый адрес кошелька для оплаты."""
        # В реальной системе здесь будет derivation из HD-кошелька или запрос к API провайдера
        return f"EQD{secrets.token_hex(16)}"

    def check_blockchain_api(self, wallet_address: str) -> dict:
        """
        Заглушка для API блокчейна. 
        В реальности здесь запрос к TON/USDT/BTC ноде или эксплореру.
        """
        raise NotImplementedError("Subclass must implement abstract method")

    def process_pending_payment(self, wallet_address: str) -> dict:
        """
        Проверяет поступление средств на указанный кошелек и выпускает слепой токен.
        Возвращает None, если платеж не подтвержден.
        """
        tx_data = self.check_blockchain_api(wallet_address)
        
        if not tx_data:
            return None
            
        if tx_data.get("status") == "confirmed" and tx_data.get("amount", 0) >= self.config["expected_amount_usd"]:
            # Платеж подтвержден, выпускаем слепой токен
            duration = self.config.get("default_token_duration_seconds", 3600)
            token_data_str = blind_tokens.generate_blind_token(
                "tariff_basic", 
                self.config["token_secret"], 
                duration
            )
            
            # Регистрация состояния в "Central DB" (для контроля устройств и явного отзыва)
            self.central_db[token_data_str] = {
                "is_active": True,
                "expiry": time.time() + duration,
                "max_devices": 1, # По умолчанию для базового тарифа
                "active_devices": 0,
                "registered_devices": []
            }
            
            return {
                "token_json": token_data_str,
                "expiry": time.time() + duration
            }
            
        return None