"""Regional profiles for anti-censorship (Russia = PRIMARY target).

If SafeNet bypasses Russian censorship (TSPU, DPI Sandvine),
it bypasses all others automatically.

Fallback order per region:
- RU: VLESS+Reality+Fragment → Trojan+TLS → AmneziaWG → WireGuard
- IR: VLESS+Reality → Trojan+TLS → WireGuard
- CN: VLESS+Reality+Fragment → Trojan+TLS → WireGuard
- TR: VLESS+Reality → Trojan+TLS → WireGuard
- AE: VLESS+Reality → Trojan+TLS → WireGuard
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class Region(str, Enum):
    RU = "RU"
    IR = "IR"
    CN = "CN"
    TR = "TR"
    AE = "AE"


class Protocol(str, Enum):
    VLESS_REALITY_FRAGMENT = "vless_reality_fragment"
    TROJAN_TLS = "trojan_tls"
    AMNEZIA_WG = "amnezia_wg"
    WIREGUARD = "wireguard"


@dataclass(frozen=True)
class SNIConfig:
    """SNI configuration per region.

    Russia (PRIMARY): google.com, cloudflare.com (most trusted, rarely blocked)
    Others: microsoft.com, apple.com (global CDN, trusted)
    """
    primary: str
    fallback: str
    fingerprint: str = "chrome"


@dataclass(frozen=True)
class FragmentConfig:
    """Fragment configuration per region.

    Russia (PRIMARY): tlshello (mandatory for TSPU bypass)
    Others: tlshello (recommended) or disabled
    """
    packets: Literal["tlshello", "1-3"] = "tlshello"
    length: str | None = None
    interval: str | None = None


@dataclass(frozen=True)
class RegionalProfile:
    """Regional anti-censorship profile.

    Contains region-specific SNI, fragment, and protocol fallback order.
    """
    region: Region
    sni: SNIConfig
    fragment: FragmentConfig
    protocol_order: list[Protocol]
    is_primary: bool = False
    description: str = ""


RUSSIA_PROFILE = RegionalProfile(
    region=Region.RU,
    sni=SNIConfig(
        primary="www.google.com",
        fallback="www.cloudflare.com",
        fingerprint="chrome",
    ),
    fragment=FragmentConfig(packets="tlshello"),
    protocol_order=[
        Protocol.VLESS_REALITY_FRAGMENT,
        Protocol.TROJAN_TLS,
        Protocol.AMNEZIA_WG,
        Protocol.WIREGUARD,
    ],
    is_primary=True,
    description="Russia (PRIMARY): TSPU + DPI Sandvine. VLESS+Reality+Fragment is mandatory.",
)

IRAN_PROFILE = RegionalProfile(
    region=Region.IR,
    sni=SNIConfig(
        primary="www.microsoft.com",
        fallback="www.apple.com",
        fingerprint="chrome",
    ),
    fragment=FragmentConfig(packets="tlshello"),
    protocol_order=[
        Protocol.VLESS_REALITY_FRAGMENT,
        Protocol.TROJAN_TLS,
        Protocol.WIREGUARD,
    ],
    description="Iran: SNI filtering + DPI. VLESS+Reality recommended.",
)

CHINA_PROFILE = RegionalProfile(
    region=Region.CN,
    sni=SNIConfig(
        primary="www.google.com",
        fallback="www.cloudflare.com",
        fingerprint="chrome",
    ),
    fragment=FragmentConfig(packets="tlshello"),
    protocol_order=[
        Protocol.VLESS_REALITY_FRAGMENT,
        Protocol.TROJAN_TLS,
        Protocol.WIREGUARD,
    ],
    description="China: GFW + SNI blocking. VLESS+Reality+Fragment mandatory.",
)

TURKEY_PROFILE = RegionalProfile(
    region=Region.TR,
    sni=SNIConfig(
        primary="www.microsoft.com",
        fallback="www.apple.com",
        fingerprint="chrome",
    ),
    fragment=FragmentConfig(packets="tlshello"),
    protocol_order=[
        Protocol.VLESS_REALITY_FRAGMENT,
        Protocol.TROJAN_TLS,
        Protocol.WIREGUARD,
    ],
    description="Turkey: SNI blocking + DPI. VLESS+Reality recommended.",
)

UAE_PROFILE = RegionalProfile(
    region=Region.AE,
    sni=SNIConfig(
        primary="www.microsoft.com",
        fallback="www.apple.com",
        fingerprint="chrome",
    ),
    fragment=FragmentConfig(packets="tlshello"),
    protocol_order=[
        Protocol.VLESS_REALITY_FRAGMENT,
        Protocol.TROJAN_TLS,
        Protocol.WIREGUARD,
    ],
    description="UAE: VoIP blocking + DPI. VLESS+Reality recommended.",
)


REGIONAL_PROFILES: dict[Region, RegionalProfile] = {
    Region.RU: RUSSIA_PROFILE,
    Region.IR: IRAN_PROFILE,
    Region.CN: CHINA_PROFILE,
    Region.TR: TURKEY_PROFILE,
    Region.AE: UAE_PROFILE,
}


def get_regional_profile(region: str | Region) -> RegionalProfile:
    """Get regional profile by region code (RU, IR, CN, TR, AE).

    Russia (RU) is PRIMARY target — if SafeNet bypasses Russian censorship,
    it bypasses all others automatically.
    """
    if isinstance(region, str):
        region = Region(region.upper())
    return REGIONAL_PROFILES[region]


def get_sni_for_region(region: str | Region, fallback: bool = False) -> str:
    """Get SNI for region (primary or fallback).

    Russia (PRIMARY): google.com (most trusted, rarely blocked by TSPU)
    Others: microsoft.com (global CDN, trusted)
    """
    profile = get_regional_profile(region)
    return profile.sni.fallback if fallback else profile.sni.primary


def get_fragment_for_region(region: str | Region) -> FragmentConfig:
    """Get fragment config for region.

    All regions use tlshello (mandatory for Russia, recommended for others).
    """
    profile = get_regional_profile(region)
    return profile.fragment


def get_protocol_order_for_region(region: str | Region) -> list[Protocol]:
    """Get protocol fallback order for region.

    Russia (PRIMARY): VLESS → Trojan → AmneziaWG → WireGuard
    Others: VLESS → Trojan → WireGuard
    """
    profile = get_regional_profile(region)
    return profile.protocol_order
