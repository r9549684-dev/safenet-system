"""
WireGuardService — генерация ключей, выделение IP-адресов, формирование конфига.
"""
import base64
import os
import random
import secrets
import subprocess
import ipaddress
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import httpx

from app.models.server import Server

log = logging.getLogger(__name__)

# Пул адресов для клиентов: 10.8.0.2 — 10.8.0.254
WG_SUBNET = ipaddress.IPv4Network("10.8.0.0/24")
WG_SERVER_IP = "10.8.0.1"
WG_CLIENT_RANGE_START = 2
WG_CLIENT_RANGE_END = 254
WG_DNS = "1.1.1.1, 1.0.0.1"

# AmneziaWG stealth-параметры (серверные, должны совпадать с wg1.conf на сервере)
# Хранятся в server.meta["stealth"], при отсутствии — эти дефолты.
# S3/S4 — для AWG 2.0 (опциональны в v2: kernel 2.0 принимает конфиг без них).
# Kernel 2.0 принимает конфиги 1.x в compat mode.
AWG_STEALTH_DEFAULTS: dict = {
    "Jc": 3,     # Junk packet count
    "Jmin": 15,  # Junk packet min size
    "Jmax": 20,  # Junk packet max size (must be > Jmin, kernel rejects Jmax <= Jmin)
    "S1": 55,    # Init packet junk size
    "S2": 25,    # Response packet junk size
    "S3": 0,     # Cookie reply junk size (AWG 2.0; 0 = disabled in v2)
    "S4": 0,     # Transport junk size  (AWG 2.0; 0 = disabled in v2)
}

# wg-manager — HTTP-прокси для управления пирами на хосте
WG_MANAGER_URL = "http://172.18.0.1:9876"

# ByeDPI-профили по коду страны (совпадают с Flutter-конфигом)
BYEDPI_PROFILES: dict[str, dict] = {
    "TR": {"split": 2, "desync": "split",    "fake_ttl": 8,  "description": "Turkey — split+fake"},
    "EG": {"split": 3, "desync": "disorder", "fake_ttl": 8,  "description": "Egypt — disorder"},
    "AE": {"split": 2, "desync": "fake",     "fake_ttl": 8,  "description": "UAE — fake"},
    "SA": {"split": 2, "desync": "fake",     "fake_ttl": 8,  "description": "Saudi Arabia — fake"},
    "PK": {"split": 3, "desync": "disorder", "fake_ttl": 6,  "description": "Pakistan — disorder"},
    "ID": {"split": 2, "desync": "split",    "fake_ttl": 6,  "description": "Indonesia — split"},
    "VE": {"split": 1, "desync": "fake",     "fake_ttl": 4,  "description": "Venezuela — fake"},
    "RU": {"split": 2, "desync": "disorder", "fake_ttl": 8,  "description": "Russia — disorder+fake"},
    "IR": {"split": 1, "desync": "fake",     "fake_ttl": 4,  "description": "Iran — full obfs"},
    "CN": {"split": 2, "desync": "split",    "fake_ttl": 6,  "description": "China — GFW bypass"},
}
DEFAULT_BYEDPI_PROFILE: dict = {"split": 2, "desync": "split", "fake_ttl": 8, "description": "Default"}


class WireGuardService:
    """Генерация WG-ключей, выделение IP, формирование клиентского конфига."""

    @staticmethod
    def generate_keypair() -> tuple[str, str]:
        """
        Генерирует пару ключей WireGuard (private, public) в base64.
        Сначала пробует через `wg genkey/pubkey`, при отсутствии wg —
        использует cryptography.hazmat (X25519).
        """
        # Генерируем raw private key (32 байта с clamping)
        raw = bytearray(os.urandom(32))
        raw[0] &= 248
        raw[31] &= 127
        raw[31] |= 64
        private_b64 = base64.b64encode(bytes(raw)).decode()

        # Пробуем wg pubkey
        try:
            result = subprocess.run(
                ["wg", "pubkey"],
                input=private_b64,
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
            public_b64 = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # Fallback: cryptography library
            try:
                from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
                priv_obj = X25519PrivateKey.from_private_bytes(bytes(raw))
                pub_raw = priv_obj.public_key().public_bytes_raw()
                public_b64 = base64.b64encode(pub_raw).decode()
            except ImportError:
                # Last resort: subprocess wg genkey (generates own private key)
                proc = subprocess.run(
                    ["wg", "genkey"], capture_output=True, text=True, check=True
                )
                private_b64 = proc.stdout.strip()
                proc2 = subprocess.run(
                    ["wg", "pubkey"],
                    input=private_b64,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                public_b64 = proc2.stdout.strip()

        return private_b64, public_b64

    @staticmethod
    async def allocate_ip(session: AsyncSession, server_id: int) -> str:
        """
        Выделяет следующий свободный IP из пула 10.8.0.2–10.8.0.254
        для данного сервера.
        """
        # Импортируем здесь чтобы избежать циклического импорта
        from app.models.connection import UserConnection

        result = await session.execute(
            select(UserConnection.allocated_ip).where(
                UserConnection.server_id == server_id,
                UserConnection.status == 'ACTIVE',
            )
        )
        used_ips = set(result.scalars().all())

        for i in range(WG_CLIENT_RANGE_START, WG_CLIENT_RANGE_END + 1):
            candidate = f"10.8.0.{i}"
            if candidate not in used_ips:
                return candidate

        raise RuntimeError(f"No free IPs available on server {server_id} (pool exhausted)")

    @staticmethod
    def _generate_h_ranges() -> dict:
        """
        Генерирует H1-H4 как строки "min-max" для AmneziaWG 2.0.
        Каждому клиенту — уникальные диапазоны; kernel 2.0 случайно
        выбирает значение внутри диапазона для каждого соединения.
          H1 — TCP seqnum offset (>=1, чтобы пакет не выглядел "пустым")
          H2 — TCP acknum offset (1 — ~2^31)
          H3 — IP.toS offset      (1 — 45, укладывается в TOS range)
          H4 — IP.ttl offset      (1 — 45, укладывается в TTL range 64)
        """
        return {
            "H1": f"{random.randint(1, 100000)}-{random.randint(100001, 2147483647)}",
            "H2": f"{random.randint(1, 100000)}-{random.randint(100001, 2147483647)}",
            "H3": f"{random.randint(1, 20)}-{random.randint(21, 45)}",
            "H4": f"{random.randint(1, 20)}-{random.randint(21, 45)}",
        }

    @staticmethod
    def _stealth_params(server: Server) -> dict:
        """
        Собирает AmneziaWG stealth-параметры для клиентского конфига.
        Версия определяется server.meta["awg_version"] (source of truth):
          - отсутствует / 1 → формат 1.x (Jc..S2, H1-H4 как int)
          - 2              → формат 2.x (+ S3/S4, + I1-I5, H1-H4 как "min-max")
        """
        meta = server.meta or {}
        srv = meta.get("stealth", AWG_STEALTH_DEFAULTS)
        awg_version = meta.get("awg_version", 1)

        # ── Общие параметры (v1 и v2) ──────────────────────────
        jmin = random.randint(10, 20)
        jmax = random.randint(jmin + 5, jmin + 15)

        stealth = {
            "Jc":   srv.get("Jc",   AWG_STEALTH_DEFAULTS["Jc"]),
            "Jmin": jmin,
            "Jmax": jmax,
            "S1":   srv.get("S1",   AWG_STEALTH_DEFAULTS["S1"]),
            "S2":   srv.get("S2",   AWG_STEALTH_DEFAULTS["S2"]),
        }

        # ── AWG 2.0: добавляем S3, S4, I1-I5, H-диапазоны ────
        if awg_version == 2:
            stealth["S3"] = srv.get("S3", AWG_STEALTH_DEFAULTS["S3"])
            stealth["S4"] = srv.get("S4", AWG_STEALTH_DEFAULTS["S4"])
            # I1-I5 — special junk strings (hex, от сервера или свежий генератор)
            # Каждый клиент получает новые строки — анти-сигнатурная защита.
            for key in ("I1", "I2", "I3", "I4", "I5"):
                stealth[key] = srv.get(key, secrets.token_hex(random.randint(2, 8)))
            stealth.update(WireGuardService._generate_h_ranges())
        else:
            # ── AWG 1.x: классический формат (H1-H4 как int) ─
            stealth["H1"] = random.randint(1, 2147483647)
            stealth["H2"] = random.randint(1, 2147483647)
            stealth["H3"] = random.randint(1, 2147483647)
            stealth["H4"] = random.randint(1, 2147483647)

        return stealth

    @staticmethod
    def generate_wg_config(
        server: Server,
        peer_private_key: str,
        peer_ip: str,
    ) -> str:
        """
        Формирует строку AmneziaWG-конфига для клиента.
        server.meta должен содержать 'wg_public_key' и опционально 'wg_port',
        'stealth' (AmneziaWG stealth-параметры).
        """
        server_pubkey = (server.meta or {}).get("wg_public_key", "SERVER_PUBLIC_KEY_PLACEHOLDER")
        server_port = (server.meta or {}).get("wg_port", server.port)
        endpoint = f"{server.host}:{server_port}"
        stealth = WireGuardService._stealth_params(server)

        stealth_block = "\n".join(f"{k} = {v}" for k, v in stealth.items())

        config = f"""[Interface]
PrivateKey = {peer_private_key}
Address = {peer_ip}/24
DNS = {WG_DNS}
{stealth_block}

[Peer]
PublicKey = {server_pubkey}
Endpoint = {endpoint}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 10
"""
        return config.strip()

    @staticmethod
    async def add_peer_to_server(pubkey: str, ip: str) -> bool:
        """
        Регистрирует пир на WireGuard-интерфейсе сервера через wg-manager.
        Возвращает True при успехе, False при недоступности wg-manager.
        Не бросает исключение — wg-manager опционален (MVP mode).
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"{WG_MANAGER_URL}/add-peer",
                    json={"pubkey": pubkey, "ip": ip},
                )
                if resp.status_code != 200:
                    log.warning("wg-manager add-peer failed: %s %s", resp.status_code, resp.text)
                    return False
                log.info("wg-manager: peer %s... added at %s", pubkey[:12], ip)
                return True
        except httpx.RequestError as e:
            log.warning("wg-manager unreachable (peer not registered on server): %s", e)
            return False

    @staticmethod
    async def remove_peer_from_server(pubkey: str) -> None:
        """
        Удаляет пир с WireGuard-интерфейса сервера через wg-manager.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"{WG_MANAGER_URL}/remove-peer",
                    json={"pubkey": pubkey},
                )
                if resp.status_code != 200:
                    log.warning("wg-manager remove-peer: %s %s", resp.status_code, resp.text)
        except httpx.RequestError as e:
            log.warning("wg-manager unreachable on remove: %s", e)

    @staticmethod
    def get_byedpi_profile(country_code: str) -> dict:
        """Возвращает ByeDPI-профиль для страны или дефолтный профиль."""
        return BYEDPI_PROFILES.get(country_code.upper(), DEFAULT_BYEDPI_PROFILE)

    @staticmethod
    async def apply_speed_limit(peer_ip: str, tier: str) -> None:
        """Устанавливает лимит скорости через wg-manager /set-speed. tier = trial|premium."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"{WG_MANAGER_URL}/set-speed",
                    json={"peer_ip": peer_ip, "tier": tier},
                )
                if resp.status_code == 200:
                    log.info("Speed limit %s set for %s: %s", tier, peer_ip, resp.json().get("result"))
                else:
                    log.warning("wg-manager set-speed failed: %s %s", resp.status_code, resp.text)
        except Exception as e:
            log.warning("apply_speed_limit failed for %s: %s", peer_ip, e)

    @staticmethod
    async def remove_speed_limit(peer_ip: str) -> None:
        """Снимает лимит скорости через wg-manager /del-speed."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"{WG_MANAGER_URL}/del-speed",
                    json={"peer_ip": peer_ip},
                )
                if resp.status_code == 200:
                    log.info("Speed limit removed for %s: %s", peer_ip, resp.json().get("result"))
                else:
                    log.warning("wg-manager del-speed failed: %s %s", resp.status_code, resp.text)
        except Exception as e:
            log.warning("remove_speed_limit failed for %s: %s", peer_ip, e)
