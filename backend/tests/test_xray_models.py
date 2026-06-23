"""Тесты VlessRealityParams (Phase 1 backend).

Проверяем контракт, который бэкенд отдаёт Flutter-клиенту.
"""
import pytest
from pydantic import ValidationError

from app.services.xray_models import (
    FragmentOpts,
    RealityOpts,
    VlessFlow,
    VlessRealityParams,
    VlessSecurity,
)


def _good(**overrides) -> dict:
    base = {
        "address": "38.180.253.219",
        "port": 2053,
        "uuid": "b2f227a9-c334-4d59-9b7f-7a16200f1e7c",
        "reality_opts": {
            "public_key": "x_9Kud4M0DXeoERCsUJZmiV-q-k6KPOUoZe20olvxnA",
            "short_id": "e95c5ddcfff353d0",
            "server_name": "www.microsoft.com",
            "fingerprint": "chrome",
        },
    }
    base.update(overrides)
    return base


# ── happy path ──────────────────────────────────────────────────────────────


def test_happy_path_defaults():
    p = VlessRealityParams(**_good())
    assert p.protocol == "vless"
    assert p.flow == VlessFlow.VISION
    assert p.security == VlessSecurity.REALITY
    assert p.fragment.packets == "tlshello"
    assert p.fragment.length is None
    assert p.fragment.interval is None


def test_happy_path_explicit_fragment():
    p = VlessRealityParams(
        **_good(
            fragment={"packets": "1-3", "length": "10-30", "interval": "10-20"}
        )
    )
    assert p.fragment.packets == "1-3"
    assert p.fragment.length == "10-30"
    assert p.fragment.interval == "10-20"


def test_reality_opts_defaults():
    """public_key/short_id обязательны; server_name/fingerprint — с дефолтами."""
    r = RealityOpts(public_key="pk", short_id="ab")
    assert r.server_name == "www.microsoft.com"
    assert r.fingerprint == "chrome"


# ── uuid валидация ──────────────────────────────────────────────────────────


def test_uuid_invalid():
    with pytest.raises(ValidationError, match="uuid"):
        VlessRealityParams(**_good(uuid="not-a-uuid"))


def test_uuid_empty():
    with pytest.raises(ValidationError):
        VlessRealityParams(**_good(uuid=""))


# ── port валидация ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("port", [0, -1, 65536, 100000])
def test_port_out_of_range(port):
    with pytest.raises(ValidationError, match="port"):
        VlessRealityParams(**_good(port=port))


@pytest.mark.parametrize("port", [1, 80, 443, 2053, 65535])
def test_port_in_range(port):
    p = VlessRealityParams(**_good(port=port))
    assert p.port == port


# ── address / public_key / short_id ─────────────────────────────────────────


def test_address_empty():
    with pytest.raises(ValidationError):
        VlessRealityParams(**_good(address=""))


def test_public_key_empty():
    with pytest.raises(ValidationError):
        VlessRealityParams(**_good(reality_opts={"public_key": "", "short_id": "ab"}))


def test_short_id_empty():
    with pytest.raises(ValidationError):
        VlessRealityParams(**_good(reality_opts={"public_key": "pk", "short_id": ""}))


def test_short_id_not_hex():
    with pytest.raises(ValidationError, match="hex"):
        VlessRealityParams(**_good(reality_opts={"public_key": "pk", "short_id": "xyz!"}))


def test_short_id_odd_hex_accepted():
    """xray принимает нечётный hex (короткие short_id)."""
    p = VlessRealityParams(**_good(reality_opts={"public_key": "pk", "short_id": "abc"}))
    assert p.reality_opts.short_id == "abc"


# ── flow enum ───────────────────────────────────────────────────────────────


def test_flow_invalid():
    with pytest.raises(ValidationError):
        VlessRealityParams(**_good(flow="xtls-rprx-direct"))  # не поддерживается


def test_flow_none_allowed():
    p = VlessRealityParams(**_good(flow="none"))
    assert p.flow == VlessFlow.NONE


# ── fragment валидация ──────────────────────────────────────────────────────


def test_fragment_invalid_length_pattern():
    with pytest.raises(ValidationError):
        VlessRealityParams(**_good(fragment={"packets": "tlshello", "length": "abc"}))


def test_fragment_invalid_packets():
    with pytest.raises(ValidationError):
        VlessRealityParams(**_good(fragment={"packets": "bogus"}))


# ── to_singbox_outbound serialization ───────────────────────────────────────


def test_to_singbox_outbound_structure():
    p = VlessRealityParams(**_good())
    ob = p.to_singbox_outbound()

    assert ob["type"] == "vless"
    assert ob["tag"] == "proxy"
    assert ob["server"] == "38.180.253.219"
    assert ob["server_port"] == 2053
    assert ob["uuid"] == "b2f227a9-c334-4d59-9b7f-7a16200f1e7c"
    assert ob["flow"] == "xtls-rprx-vision"
    # tls блок
    assert ob["tls"]["enabled"] is True
    assert ob["tls"]["server_name"] == "www.microsoft.com"
    assert ob["tls"]["utls"]["fingerprint"] == "chrome"
    assert ob["tls"]["reality"]["public_key"] == "x_9Kud4M0DXeoERCsUJZmiV-q-k6KPOUoZe20olvxnA"
    assert ob["tls"]["reality"]["short_id"] == "e95c5ddcfff353d0"
    # fragment блок
    assert ob["fragment"]["packets"] == "tlshello"
    # length/interval НЕ попадут, когда None
    assert "length" not in ob["fragment"]
    assert "interval" not in ob["fragment"]


def test_to_singbox_outbound_no_transport_tcp():
    """sing-box 1.12+ FATAL на transport.type=tcp + vision flow — НЕ ставим."""
    p = VlessRealityParams(**_good())
    ob = p.to_singbox_outbound()
    assert "transport" not in ob


def test_to_singbox_outbound_server_override():
    p = VlessRealityParams(**_good())
    ob = p.to_singbox_outbound(server="cdn.example.com")
    assert ob["server"] == "cdn.example.com"


def test_to_singbox_outbound_fragment_explicit():
    p = VlessRealityParams(
        **_good(fragment={"packets": "1-3", "length": "10-30", "interval": "10-20"})
    )
    ob = p.to_singbox_outbound()
    assert ob["fragment"]["packets"] == "1-3"
    assert ob["fragment"]["length"] == "10-30"
    assert ob["fragment"]["interval"] == "10-20"


# ── model_dump (сериализация для API) ───────────────────────────────────────


def test_model_dump_keeps_structure():
    """FastAPI использует .model_dump() через response_model."""
    p = VlessRealityParams(**_good())
    dumped = p.model_dump()
    # поле должно быть именем 'reality_opts' (Flutter ожидает именно это)
    assert "reality_opts" in dumped
    assert "public_key" in dumped["reality_opts"]
    assert dumped["flow"] == "xtls-rprx-vision"
    assert dumped["fragment"]["packets"] == "tlshello"


def test_model_dump_json_roundtrip():
    import json
    p = VlessRealityParams(**_good())
    raw = p.model_dump_json()
    parsed = json.loads(raw)
    assert parsed["uuid"] == "b2f227a9-c334-4d59-9b7f-7a16200f1e7c"
    assert parsed["fragment"]["packets"] == "tlshello"
