import json
import time
from typing import Dict, Any, List

class GossipNode:
    def __init__(self, node_id: str, config_path: str, crypto_module):
        self.node_id = node_id
        self.config_path = config_path
        self.crypto = crypto_module
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
        self.state = {
            "gateways": {},
            "revoked_tokens": {},
            "node_status": {}
        }
        self.update_log = {}
        self.blacklist = set()
        self.outgoing_buffer = []

    def create_signed_update(self, payload: dict) -> dict:
        """Создает криптографически подписанное обновление."""
        update_id = f"{self.node_id}_{int(time.time() * 1000)}"
        # Подписываются только неизменяемые данные (hops вынесен наружу)
        update_data = {
            "update_id": update_id,
            "source_node": self.node_id,
            "timestamp": time.time(),
            "payload": payload
        }
        signature = self.crypto.sign_data(update_data)
        signed_update = {
            "data": update_data,
            "hops": 0,
            "signature": signature.hex(),
            "public_key_bytes": self.crypto.get_public_key_bytes().hex()
        }
        self.outgoing_buffer.append(signed_update)
        self._process_validated_update(update_data)
        self.update_log[update_id] = {"timestamp": update_data["timestamp"], "source": self.node_id}
        return signed_update

    def apply_update(self, signed_update: dict, trusted_source_node_id: str):
        """Применяет обновление локально (например, после собственной генерации)."""
        self._process_validated_update(signed_update["data"])

    def receive_update(self, signed_update: dict) -> dict:
        """Принимает обновление от пира, проверяет подпись и применяет LWW."""
        data = signed_update["data"]
        signature = bytes.fromhex(signed_update["signature"])
        source_node = data["source_node"]
        
        # 1. Проверка черного списка
        if source_node in self.blacklist:
            return {"success": False, "reason": "source_blacklisted"}

        # 2. Криптографическая проверка подписи
        is_valid = self.crypto.verify_signature(data, signature, self.crypto.public_key)
        if not is_valid:
            self.blacklist.add(source_node)
            return {"success": False, "reason": "invalid_signature"}

        # 3. Защита от петель и устаревших данных (Last Write Wins - LWW)
        update_id = data["update_id"]
        if update_id in self.update_log:
            if data["timestamp"] <= self.update_log[update_id]["timestamp"]:
                return {"success": False, "reason": "stale_update"}

        # 4. Ограничение глубины рассылки (TTL)
        if signed_update.get("hops", 0) >= self.config.get("max_hops", 5):
            return {"success": False, "reason": "max_hops_exceeded"}

        # 5. Применение обновления
        self._process_validated_update(data)
        self.update_log[update_id] = {"timestamp": data["timestamp"], "source": source_node}
        
        # 6. Добавляем в исходящий буфер для дальнейшей лавинообразной рассылки (Gossip)
        forward_update = {
            "data": data,
            "hops": signed_update.get("hops", 0) + 1,
            "signature": signed_update["signature"],
            "public_key_bytes": signed_update["public_key_bytes"]
        }
        self.outgoing_buffer.append(forward_update)
        
        return {"success": True, "reason": "applied"}

    def _process_validated_update(self, data: dict):
        """Внутренняя логика слияния состояния (Conflict Resolution - Last Write Wins)."""
        payload = data["payload"]
        p_type = payload.get("type")
        target_id = payload.get("gateway_id") or payload.get("token_id") or payload.get("target_node")
        
        if p_type == "gateway_update":
            current = self.state["gateways"].get(target_id, {})
            if data["timestamp"] > current.get("timestamp", 0):
                self.state["gateways"][target_id] = {**payload["data"], "timestamp": data["timestamp"]}
                
        elif p_type == "token_revoke":
            current = self.state["revoked_tokens"].get(target_id, {})
            if data["timestamp"] > current.get("timestamp", 0):
                self.state["revoked_tokens"][target_id] = {**payload["data"], "timestamp": data["timestamp"]}
                
        elif p_type == "node_ban":
            current = self.state["node_status"].get(target_id, {})
            if data["timestamp"] > current.get("timestamp", 0):
                self.state["node_status"][target_id] = {**payload["data"], "timestamp": data["timestamp"], "banned": True}

    def get_pending_updates(self) -> List[dict]:
        """Возвращает все обновления, которые нужно разослать пирам, и очищает буфер."""
        buffer = self.outgoing_buffer.copy()
        self.outgoing_buffer.clear()
        return buffer

    def is_token_revoked(self, token_id: str) -> bool:
        """Проверяет, отозван ли токен в локальном реестре."""
        return token_id in self.state["revoked_tokens"]