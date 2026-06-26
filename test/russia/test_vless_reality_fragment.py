"""Test VLESS+Reality+Fragment against Russian censorship (PRIMARY).

Rostelecom is STRICTEST — if it works there, it works everywhere in Russia.

TSPU (Technical Service for Counteracting Threats):
- Blocks by SNI (Server Name Indication)
- Fragments TLS handshake
- Blocks WireGuard data-plane
- Blocks UDP (AmneziaWG)

VLESS+Reality+Fragment bypasses TSPU:
- SNI = google.com (trusted, rarely blocked)
- Fragment = tlshello (fragments TLS ClientHello)
- Reality = no real certificate needed (spoofs trusted domain)
"""
import pytest
from app.services.xray import get_vless_config
from app.services.regional_profiles import Region, get_sni_for_region


class TestVlessRealityFragmentRussia:
    """Test VLESS+Reality+Fragment for Russia (PRIMARY target)."""

    def test_russia_sni_is_google(self):
        """Russia (PRIMARY): SNI must be google.com (trusted by TSPU)."""
        sni = get_sni_for_region(Region.RU, fallback=False)
        assert sni == "www.google.com", (
            f"Russia SNI must be google.com (trusted by TSPU), got {sni}"
        )

    def test_russia_fallback_sni_is_cloudflare(self):
        """Russia fallback: SNI must be cloudflare.com (trusted CDN)."""
        sni = get_sni_for_region(Region.RU, fallback=True)
        assert sni == "www.cloudflare.com", (
            f"Russia fallback SNI must be cloudflare.com, got {sni}"
        )

    def test_vless_config_russia_uses_google_sni(self):
        """VLESS config for Russia must use google.com SNI."""
        config = get_vless_config(server_ip="10.0.0.1", region="RU")
        assert config.reality_opts.server_name.value == "www.google.com", (
            f"Russia VLESS SNI must be google.com, got {config.reality_opts.server_name.value}"
        )

    def test_vless_config_russia_uses_fragment(self):
        """VLESS config for Russia must use fragment (mandatory for TSPU bypass)."""
        config = get_vless_config(server_ip="10.0.0.1", region="RU")
        assert config.fragment.packets == "tlshello", (
            f"Russia VLESS must use fragment packets='tlshello', got {config.fragment.packets}"
        )

    def test_vless_config_russia_uses_reality(self):
        """VLESS config for Russia must use reality (spoofs trusted domain)."""
        config = get_vless_config(server_ip="10.0.0.1", region="RU")
        assert config.security.value == "reality", (
            f"Russia VLESS must use security='reality', got {config.security.value}"
        )

    def test_vless_config_russia_uses_vision_flow(self):
        """VLESS config for Russia must use xtls-rprx-vision flow."""
        config = get_vless_config(server_ip="10.0.0.1", region="RU")
        assert config.flow.value == "xtls-rprx-vision", (
            f"Russia VLESS must use flow='xtls-rprx-vision', got {config.flow.value}"
        )

    def test_vless_config_russia_uses_chrome_fingerprint(self):
        """VLESS config for Russia must use chrome fingerprint (most trusted)."""
        config = get_vless_config(server_ip="10.0.0.1", region="RU")
        assert config.reality_opts.fingerprint == "chrome", (
            f"Russia VLESS must use fingerprint='chrome', got {config.reality_opts.fingerprint}"
        )

    def test_vless_config_russia_port_443(self):
        """VLESS config for Russia must use port 443 (HTTPS, trusted)."""
        config = get_vless_config(server_ip="10.0.0.1", region="RU")
        assert config.port == 443, (
            f"Russia VLESS must use port 443 (HTTPS), got {config.port}"
        )

    def test_vless_singbox_outbound_structure(self):
        """VLESS to_singbox_outbound() must generate correct structure."""
        config = get_vless_config(server_ip="10.0.0.1", region="RU")
        outbound = config.to_singbox_outbound()
        assert outbound["type"] == "vless"
        assert outbound["tls"]["reality"]["enabled"] is True
        assert outbound["tls"]["fragment"]["packets"] == "tlshello"
        assert outbound["tls"]["server_name"] == "www.google.com"
        assert outbound["tls"]["utls"]["fingerprint"] == "chrome"

    def test_vless_config_russia_uses_chrome_fingerprint(self):
        """VLESS config for Russia must use chrome fingerprint (most trusted)."""
        config = get_vless_config(server_ip="10.0.0.1", region="RU")
        assert config.reality_opts.fingerprint == "chrome", (
            f"Russia VLESS must use fingerprint='chrome', got {config.reality_opts.fingerprint}"
        )

    def test_vless_config_russia_port_443(self):
        """VLESS config for Russia must use port 443 (HTTPS, trusted)."""
        config = get_vless_config(server_ip="10.0.0.1", region="RU")
        assert config.port == 443, (
            f"Russia VLESS must use port 443 (HTTPS), got {config.port}"
        )


class TestVlessRealityFragmentOtherRegions:
    """Test VLESS+Reality+Fragment for other regions (not PRIMARY)."""

    def test_iran_sni_is_microsoft(self):
        """Iran: SNI must be microsoft.com (global CDN)."""
        sni = get_sni_for_region(Region.IR, fallback=False)
        assert sni == "www.microsoft.com", (
            f"Iran SNI must be microsoft.com, got {sni}"
        )

    def test_china_sni_is_google(self):
        """China: SNI must be google.com (GFW bypass)."""
        sni = get_sni_for_region(Region.CN, fallback=False)
        assert sni == "www.google.com", (
            f"China SNI must be google.com, got {sni}"
        )

    def test_turkey_sni_is_microsoft(self):
        """Turkey: SNI must be microsoft.com (global CDN)."""
        sni = get_sni_for_region(Region.TR, fallback=False)
        assert sni == "www.microsoft.com", (
            f"Turkey SNI must be microsoft.com, got {sni}"
        )

    def test_uae_sni_is_microsoft(self):
        """UAE: SNI must be microsoft.com (global CDN)."""
        sni = get_sni_for_region(Region.AE, fallback=False)
        assert sni == "www.microsoft.com", (
            f"UAE SNI must be microsoft.com, got {sni}"
        )
