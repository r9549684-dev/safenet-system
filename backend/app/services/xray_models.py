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


class RealityOpts(BaseModel):
    """Reality-параметры (подблок tls.reality + tls.utls)."""

    public_key: str = Field(..., min_length=1)
    short_id: str = Field(..., min_length=1)
    server_name: str = Field(default="www.microsoft.com", min_length=1)
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
                "server_name": self.reality_opts.server_name,
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
