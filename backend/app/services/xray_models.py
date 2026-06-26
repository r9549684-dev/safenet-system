"""Pydantic-модель VLESS+Reality конфига (Phase 1).

Контракт между backend и Flutter-клиентом:
- Типизированный VlessRealityParams (ранее — сырой dict[str, Any]).
- UUID v4, port 1-65535, непустые public_key/short_id.
- Flow строго из enum'а (xtls-rprx-vision — единственный поддерживаемый).
- Fragment: всегда включён, значение по умолчанию packets="tlshello".
"""
from __future__ import annotations

from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class VlessFlow(str, Enum):
    """Поддерживаемые VLESS flow-режимы.

    xtls-rprx-vision — единственный production flow для Reality.
    none — только для тестов (без utls/reality, не используется).
    """

    VISION = "xtls-rprx-vision"
    NONE = "none"


class VlessSecurity(str, Enum):
    NONE = "none"
    REALITY = "reality"


class AllowedSNI(str, Enum):
    """Allowed SNI values for anti-censorship.

    Russia (PRIMARY): google.com, cloudflare.com (trusted by TSPU)
    Others: microsoft.com, apple.com (global CDN, trusted)
    """
    GOOGLE = "www.google.com"
    CLOUDFLARE = "www.cloudflare.com"
    MICROSOFT = "www.microsoft.com"
    APPLE = "www.apple.com"


class RealityOpts(BaseModel):
    """Reality-параметры (подблок tls.reality + tls.utls)."""

    public_key: str = Field(..., min_length=1)
    short_id: str = Field(..., min_length=1)
    server_name: AllowedSNI = Field(default=AllowedSNI.MICROSOFT)
    fingerprint: str = Field(default="chrome", min_length=1)

    @field_validator("short_id")
    @classmethod
    def _short_id_hex(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("short_id пустой")
        # допускаем чётный и нечётный hex (xray принимает оба)
        try:
            int(cleaned, 16)
        except ValueError as e:
            raise ValueError(f"short_id должен быть hex-строкой, получено: {v!r}") from e
        return cleaned


class FragmentOpts(BaseModel):
    """Fragment-опции для обхода L7 DPI fingerprint.

    sing-box формат: {packets: "tlshello"} — фрагментирует TLS ClientHello.
    xray-core совместимый формат: {packets, length, interval}.
    Модель принимает оба (length/interval опциональны).
    """

    packets: Literal["tlshello", "1-3"] = "tlshello"
    length: str | None = Field(default=None, pattern=r"^\d+-\d+$")
    interval: str | None = Field(default=None, pattern=r"^\d+-\d+$")


class VlessRealityParams(BaseModel):
    """Полный VLESS+Reality+Fragment конфиг для клиента.

    Заменяет сырой dict[str, Any], выдаваемый раньше из get_vless_config().
    """

    protocol: Literal["vless"] = "vless"
    address: str = Field(..., min_length=1)
    port: int = Field(..., ge=1, le=65535)
    uuid: str = Field(..., min_length=1)
    flow: VlessFlow = VlessFlow.VISION
    security: VlessSecurity = VlessSecurity.REALITY
    reality_opts: RealityOpts
    fragment: FragmentOpts = Field(default_factory=FragmentOpts)

    @field_validator("uuid")
    @classmethod
    def _uuid_valid(cls, v: str) -> str:
        try:
            UUID(v)
        except ValueError as e:
            raise ValueError(f"uuid должен быть валидным UUID: {v!r}") from e
        return v

    def to_singbox_outbound(self, *, server: str | None = None, tag: str = "proxy") -> dict:
        """Собирает sing-box outbound-блок (без полного конфига — только outbounds[0]).

        `server` перезаписывает address (для случаев, когда клиент соединяется через CDN).
        """
        addr = server or self.address
        return {
            "type": "vless",
            "tag": tag,
            "server": addr,
            "server_port": self.port,
            "uuid": self.uuid,
            "flow": self.flow.value,
            "tls": {
                "enabled": True,
                "server_name": self.reality_opts.server_name.value,
                "utls": {
                    "enabled": True,
                    "fingerprint": self.reality_opts.fingerprint,
                },
                "reality": {
                    "enabled": True,
                    "public_key": self.reality_opts.public_key,
                    "short_id": self.reality_opts.short_id,
                },
                "fragment": self.fragment.model_dump(exclude_none=True),
            },
        }


class TrojanParams(BaseModel):
    """Trojan+TLS конфиг для клиента.

    Trojan маскируется под обычный HTTPS трафик, обходя DPI.
    
    RISK: insecure=True отключает проверку TLS-сертификата (MITM уязвимость).
    Для production рекомендуется использовать certificate_fingerprint для pinning.
    """

    protocol: Literal["trojan"] = "trojan"
    address: str = Field(..., min_length=1)
    port: int = Field(..., ge=1, le=65535)
    password: str = Field(..., min_length=1)
    sni: AllowedSNI = Field(default=AllowedSNI.MICROSOFT)
    insecure: bool = Field(default=False)
    certificate_fingerprint: str | None = Field(default=None)

    def to_singbox_outbound(self, *, server: str | None = None, tag: str = "proxy") -> dict:
        """Собирает sing-box outbound-блок для Trojan."""
        addr = server or self.address
        tls_config = {
            "enabled": True,
            "server_name": self.sni.value,
            "insecure": self.insecure,
        }
        if self.certificate_fingerprint:
            tls_config["certificate_fingerprint"] = self.certificate_fingerprint
        return {
            "type": "trojan",
            "tag": tag,
            "server": addr,
            "server_port": self.port,
            "password": self.password,
            "tls": tls_config,
        }


class AmneziaWGParams(BaseModel):
    """AmneziaWG (обфусцированный WireGuard) конфиг для клиента.

    AmneziaWG — это обфусцированный WireGuard для обхода DPI.
    Использует UDP с обфускацией для маскировки под обычный трафик.
    
    WARNING: В России AmneziaWG блокируется DPI (data-plane мёртв).
    Используется только как fallback_2 после VLESS и Trojan.
    
    Обфускация:
    - Jc (Junk packets): случайные пакеты для маскировки
    - Jmin, Jmax: минимальный/максимальный размер junk packets
    - S1, S2: размеры обфусцированных пакетов
    - H1, H2, H3: хэши для обфускации
    """

    protocol: Literal["amneziawg"] = "amneziawg"
    address: str = Field(..., min_length=1)
    port: int = Field(..., ge=1, le=65535)
    private_key: str = Field(..., min_length=1)
    public_key: str = Field(..., min_length=1)
    preshared_key: str | None = Field(default=None)
    ip: str = Field(default="10.0.0.2")
    dns: list[str] = Field(default_factory=lambda: ["1.1.1.1", "8.8.8.8"])
    mtu: int = Field(default=1420)
    
    # AmneziaWG obfuscation params
    jc: int = Field(default=3, ge=1, le=10)
    jmin: int = Field(default=50, ge=10, le=1000)
    jmax: int = Field(default=1000, ge=100, le=10000)
    s1: int = Field(default=55, ge=1, le=100)
    s2: int = Field(default=110, ge=1, le=200)
    h1: int = Field(default=123456789, ge=1)
    h2: int = Field(default=987654321, ge=1)
    h3: int = Field(default=112233445, ge=1)

    def to_singbox_outbound(self, *, server: str | None = None, tag: str = "proxy") -> dict:
        """Собирает sing-box outbound-блок для AmneziaWG."""
        addr = server or self.address
        return {
            "type": "wireguard",
            "tag": tag,
            "server": addr,
            "server_port": self.port,
            "local_address": [self.ip],
            "private_key": self.private_key,
            "peer_public_key": self.public_key,
            "pre_shared_key": self.preshared_key,
            "dns_servers": self.dns,
            "mtu": self.mtu,
            "amnezia": {
                "jc": self.jc,
                "jmin": self.jmin,
                "jmax": self.jmax,
                "s1": self.s1,
                "s2": self.s2,
                "h1": self.h1,
                "h2": self.h2,
                "h3": self.h3,
            },
        }
