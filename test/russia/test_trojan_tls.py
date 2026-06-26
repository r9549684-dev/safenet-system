"""Test Trojan+TLS against Russian censorship (fallback_1).

Rostelecom is STRICTEST — if Trojan works there, it works everywhere in Russia.

Trojan+TLS bypasses TSPU:
- SNI = google.com (trusted, rarely blocked)
- TLS = real HTTPS traffic (looks like normal browsing)
- Port 443 = HTTPS (trusted)

Trojan is fallback_1 after VLESS+Reality+Fragment.
"""
import pytest
from app.services.xray import get_trojan_config
from app.services.regional_profiles import Region, get_sni_for_region


class TestTrojanTlsRussia:
    """Test Trojan+TLS for Russia (fallback_1)."""

    def test_trojan_config_russia_uses_google_sni(self):
        """Trojan config for Russia must use google.com SNI."""
        config = get_trojan_config(server_ip="10.0.0.1", region="RU")
        assert config.sni.value == "www.google.com", (
            f"Russia Trojan SNI must be google.com, got {config.sni.value}"
        )

    def test_trojan_config_russia_uses_tls(self):
        """Trojan config for Russia must use TLS (looks like normal HTTPS).
        
        RISK: insecure=True for self-signed cert (MITM risk).
        This is acceptable for anti-censorship but should be documented.
        """
        config = get_trojan_config(server_ip="10.0.0.1", region="RU")
        assert config.insecure is True, (
            "Russia Trojan must use insecure=True (self-signed cert for anti-censorship)"
        )

    def test_trojan_config_russia_port_443(self):
        """Trojan config for Russia must use port 443 (HTTPS, trusted)."""
        config = get_trojan_config(server_ip="10.0.0.1", region="RU")
        assert config.port == 443, (
            f"Russia Trojan must use port 443 (HTTPS), got {config.port}"
        )

    def test_trojan_config_russia_protocol(self):
        """Trojan config for Russia must use trojan protocol."""
        config = get_trojan_config(server_ip="10.0.0.1", region="RU")
        assert config.protocol == "trojan", (
            f"Russia Trojan must use protocol='trojan', got {config.protocol}"
        )

    def test_trojan_singbox_outbound_structure(self):
        """Trojan to_singbox_outbound() must generate correct structure."""
        config = get_trojan_config(server_ip="10.0.0.1", region="RU")
        outbound = config.to_singbox_outbound()
        assert outbound["type"] == "trojan"
        assert outbound["tls"]["enabled"] is True
        assert outbound["tls"]["server_name"] == "www.google.com"
        assert outbound["server_port"] == 443


class TestTrojanTlsOtherRegions:
    """Test Trojan+TLS for other regions (not PRIMARY)."""

    def test_trojan_config_iran_uses_microsoft_sni(self):
        """Trojan config for Iran must use microsoft.com SNI."""
        config = get_trojan_config(server_ip="10.0.0.1", region="IR")
        assert config.sni.value == "www.microsoft.com", (
            f"Iran Trojan SNI must be microsoft.com, got {config.sni.value}"
        )

    def test_trojan_config_china_uses_google_sni(self):
        """Trojan config for China must use google.com SNI (GFW bypass)."""
        config = get_trojan_config(server_ip="10.0.0.1", region="CN")
        assert config.sni.value == "www.google.com", (
            f"China Trojan SNI must be google.com, got {config.sni.value}"
        )

    def test_trojan_config_turkey_uses_microsoft_sni(self):
        """Trojan config for Turkey must use microsoft.com SNI."""
        config = get_trojan_config(server_ip="10.0.0.1", region="TR")
        assert config.sni.value == "www.microsoft.com", (
            f"Turkey Trojan SNI must be microsoft.com, got {config.sni.value}"
        )

    def test_trojan_config_uae_uses_microsoft_sni(self):
        """Trojan config for UAE must use microsoft.com SNI."""
        config = get_trojan_config(server_ip="10.0.0.1", region="AE")
        assert config.sni.value == "www.microsoft.com", (
            f"UAE Trojan SNI must be microsoft.com, got {config.sni.value}"
        )
