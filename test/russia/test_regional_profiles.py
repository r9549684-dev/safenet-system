"""Test regional profiles for anti-censorship.

Russia (RU) is PRIMARY target — if SafeNet bypasses Russian censorship,
it bypasses all others automatically.

Protocol fallback order per region:
- RU: VLESS+Reality+Fragment → Trojan+TLS → AmneziaWG → WireGuard
- IR: VLESS+Reality → Trojan+TLS → WireGuard
- CN: VLESS+Reality+Fragment → Trojan+TLS → WireGuard
- TR: VLESS+Reality → Trojan+TLS → WireGuard
- AE: VLESS+Reality → Trojan+TLS → WireGuard
"""
import pytest
from app.services.regional_profiles import (
    Region,
    Protocol,
    get_regional_profile,
    get_sni_for_region,
    get_fragment_for_region,
    get_protocol_order_for_region,
    RUSSIA_PROFILE,
)


class TestRegionalProfiles:
    """Test regional profiles for anti-censorship."""

    def test_russia_is_primary(self):
        """Russia must be PRIMARY target."""
        profile = get_regional_profile(Region.RU)
        assert profile.is_primary is True, "Russia must be PRIMARY target"

    def test_russia_protocol_order(self):
        """Russia protocol order: VLESS → Trojan → AmneziaWG → WireGuard."""
        order = get_protocol_order_for_region(Region.RU)
        assert order == [
            Protocol.VLESS_REALITY_FRAGMENT,
            Protocol.TROJAN_TLS,
            Protocol.AMNEZIA_WG,
            Protocol.WIREGUARD,
        ], f"Russia protocol order incorrect: {order}"

    def test_iran_protocol_order(self):
        """Iran protocol order: VLESS → Trojan → WireGuard (no AmneziaWG)."""
        order = get_protocol_order_for_region(Region.IR)
        assert order == [
            Protocol.VLESS_REALITY_FRAGMENT,
            Protocol.TROJAN_TLS,
            Protocol.WIREGUARD,
        ], f"Iran protocol order incorrect: {order}"

    def test_china_protocol_order(self):
        """China protocol order: VLESS → Trojan → WireGuard (no AmneziaWG)."""
        order = get_protocol_order_for_region(Region.CN)
        assert order == [
            Protocol.VLESS_REALITY_FRAGMENT,
            Protocol.TROJAN_TLS,
            Protocol.WIREGUARD,
        ], f"China protocol order incorrect: {order}"

    def test_russia_sni_google(self):
        """Russia SNI must be google.com (trusted by TSPU)."""
        sni = get_sni_for_region(Region.RU, fallback=False)
        assert sni == "www.google.com", f"Russia SNI must be google.com, got {sni}"

    def test_russia_fallback_sni_cloudflare(self):
        """Russia fallback SNI must be cloudflare.com (trusted CDN)."""
        sni = get_sni_for_region(Region.RU, fallback=True)
        assert sni == "www.cloudflare.com", f"Russia fallback SNI must be cloudflare.com, got {sni}"

    def test_russia_fragment_tlshello(self):
        """Russia fragment must be tlshello (mandatory for TSPU bypass)."""
        fragment = get_fragment_for_region(Region.RU)
        assert fragment.packets == "tlshello", (
            f"Russia fragment must be tlshello, got {fragment.packets}"
        )

    def test_all_regions_use_tlshello_fragment(self):
        """All regions must use tlshello fragment (recommended for all)."""
        for region in Region:
            fragment = get_fragment_for_region(region)
            assert fragment.packets == "tlshello", (
                f"Region {region} must use tlshello fragment, got {fragment.packets}"
            )

    def test_russia_profile_description(self):
        """Russia profile must mention TSPU + DPI Sandvine."""
        profile = RUSSIA_PROFILE
        assert "TSPU" in profile.description, "Russia description must mention TSPU"
        assert "DPI" in profile.description, "Russia description must mention DPI"

    def test_russia_profile_is_primary(self):
        """Russia profile must be marked as PRIMARY."""
        profile = RUSSIA_PROFILE
        assert profile.is_primary is True, "Russia profile must be PRIMARY"
