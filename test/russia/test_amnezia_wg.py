"""Test AmneziaWG against Russian censorship (fallback_2).

WARNING: AmneziaWG is BLOCKED by DPI in Russia (data-plane dead).
Used only as fallback_2 after VLESS and Trojan.

AmneziaWG bypasses some DPI:
- Uses UDP with obfuscation (Jc, Jmin, Jmax, S1, S2, H1, H2, H3)
- Masks as random UDP traffic
- Port 51820 (default WireGuard port)

However, Russian DPI (TSPU, Sandvine) detects AmneziaWG data-plane.
"""
import pytest
from app.services.xray import get_amnezia_config
from app.services.regional_profiles import Region


class TestAmneziaWGRussia:
    """Test AmneziaWG for Russia (fallback_2)."""

    def test_amnezia_config_russia_port_51820(self):
        """AmneziaWG config for Russia must use port 51820 (default WireGuard)."""
        config = get_amnezia_config(server_ip="10.0.0.1", region="RU")
        assert config.port == 51820, (
            f"Russia AmneziaWG must use port 51820 (WireGuard default), got {config.port}"
        )

    def test_amnezia_config_russia_protocol(self):
        """AmneziaWG config for Russia must use amneziawg protocol."""
        config = get_amnezia_config(server_ip="10.0.0.1", region="RU")
        assert config.protocol == "amneziawg", (
            f"Russia AmneziaWG must use protocol='amneziawg', got {config.protocol}"
        )

    def test_amnezia_config_russia_has_obfuscation_params(self):
        """AmneziaWG config for Russia must have obfuscation params."""
        config = get_amnezia_config(server_ip="10.0.0.1", region="RU")
        assert config.jc == 3, f"AmneziaWG must have jc=3, got {config.jc}"
        assert config.jmin == 50, f"AmneziaWG must have jmin=50, got {config.jmin}"
        assert config.jmax == 1000, f"AmneziaWG must have jmax=1000, got {config.jmax}"
        assert config.s1 == 55, f"AmneziaWG must have s1=55, got {config.s1}"
        assert config.s2 == 110, f"AmneziaWG must have s2=110, got {config.s2}"
        assert config.h1 == 123456789, f"AmneziaWG must have h1=123456789, got {config.h1}"
        assert config.h2 == 987654321, f"AmneziaWG must have h2=987654321, got {config.h2}"
        assert config.h3 == 112233445, f"AmneziaWG must have h3=112233445, got {config.h3}"

    def test_amnezia_config_russia_has_keys(self):
        """AmneziaWG config for Russia must have private/public keys."""
        config = get_amnezia_config(server_ip="10.0.0.1", region="RU")
        assert config.private_key, "AmneziaWG must have private_key"
        assert config.public_key, "AmneziaWG must have public_key"

    def test_amnezia_config_russia_has_dns(self):
        """AmneziaWG config for Russia must have DNS servers."""
        config = get_amnezia_config(server_ip="10.0.0.1", region="RU")
        assert len(config.dns) >= 2, "AmneziaWG must have at least 2 DNS servers"
        assert "1.1.1.1" in config.dns, "AmneziaWG must have 1.1.1.1 DNS"
        assert "8.8.8.8" in config.dns, "AmneziaWG must have 8.8.8.8 DNS"

    def test_amnezia_singbox_outbound_structure(self):
        """AmneziaWG to_singbox_outbound() must generate correct structure."""
        config = get_amnezia_config(server_ip="10.0.0.1", region="RU")
        outbound = config.to_singbox_outbound()
        assert outbound["type"] == "wireguard"
        assert outbound["server_port"] == 51820
        assert "amnezia" in outbound
        assert outbound["amnezia"]["jc"] == 3
        assert outbound["amnezia"]["jmin"] == 50
        assert outbound["amnezia"]["jmax"] == 1000


class TestAmneziaWGBlockedInRussia:
    """Test that AmneziaWG is documented as blocked in Russia."""

    def test_amnezia_is_blocked_by_dpi(self):
        """AmneziaWG is blocked by Russian DPI (data-plane dead).
        
        This test documents the fact that AmneziaWG doesn't work in Russia.
        It's used only as fallback_2 after VLESS and Trojan.
        """
        config = get_amnezia_config(server_ip="10.0.0.1", region="RU")
        assert config.protocol == "amneziawg"
        # Documentation: AmneziaWG is blocked by Russian DPI (TSPU, Sandvine)
        # Use VLESS+Reality+Fragment (primary) or Trojan+TLS (fallback_1) instead
