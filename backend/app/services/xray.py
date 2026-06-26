from app.config import settings
from app.services.xray_models import (
    FragmentOpts, RealityOpts, VlessRealityParams, TrojanParams, AmneziaWGParams, AllowedSNI
)
from app.services.regional_profiles import (
    Region,
    get_sni_for_region,
    get_fragment_for_region,
)


def get_vless_config(server_ip: str, region: str = "RU") -> VlessRealityParams:
    """Возвращает типизированный VLESS+Reality+Fragment конфиг для клиента.

    Контракт: всегда включает fragment (tlshello), security="reality",
    flow="xtls-rprx-vision". См. xray_models.VlessRealityParams.

    Россия (PRIMARY): SNI = google.com (обходит TSPU)
    Другие регионы: SNI = microsoft.com (глобальный CDN)
    """
    sni_str = get_sni_for_region(region, fallback=False)
    sni = AllowedSNI(sni_str)
    fragment_cfg = get_fragment_for_region(region)

    return VlessRealityParams(
        protocol="vless",
        address=server_ip,
        port=settings.XRAY_PORT,
        uuid=settings.XRAY_UUID,
        flow="xtls-rprx-vision",
        security="reality",
        reality_opts=RealityOpts(
            public_key=settings.XRAY_PUBLIC_KEY,
            short_id=settings.XRAY_SHORT_ID,
            server_name=sni,
            fingerprint="chrome",
        ),
        fragment=FragmentOpts(
            packets=fragment_cfg.packets,
            length=fragment_cfg.length,
            interval=fragment_cfg.interval,
        ),
    )


def get_trojan_config(server_ip: str, region: str = "RU") -> TrojanParams:
    """Возвращает типизированный Trojan+TLS конфиг для клиента.

    Trojan маскируется под HTTPS трафик, обходя DPI.

    Россия (PRIMARY): SNI = google.com (обходит TSPU)
    Другие регионы: SNI = microsoft.com (глобальный CDN)
    
    RISK: insecure=True для self-signed cert (MITM risk).
    Для production рекомендуется certificate_fingerprint.
    """
    sni_str = get_sni_for_region(region, fallback=False)
    sni = AllowedSNI(sni_str)

    return TrojanParams(
        protocol="trojan",
        address=server_ip,
        port=settings.TROJAN_PORT,
        password=settings.TROJAN_PASSWORD,
        sni=sni,
        insecure=True,
    )


def get_amnezia_config(server_ip: str, region: str = "RU") -> AmneziaWGParams:
    """Возвращает типизированный AmneziaWG конфиг для клиента.

    AmneziaWG — обфусцированный WireGuard для обхода DPI.
    Использует UDP с обфускацией (Jc, Jmin, Jmax, S1, S2, H1, H2, H3).
    
    WARNING: В России AmneziaWG блокируется DPI (data-plane мёртв).
    Используется только как fallback_2 после VLESS и Trojan.
    
    Россия (PRIMARY): fallback_2 (после VLESS и Trojan)
    Другие регионы: fallback_2 (после VLESS и Trojan)
    """
    return AmneziaWGParams(
        protocol="amneziawg",
        address=server_ip,
        port=settings.AMNEZIA_PORT,
        private_key=settings.AMNEZIA_PRIVATE_KEY,
        public_key=settings.AMNEZIA_PUBLIC_KEY,
        preshared_key=settings.AMNEZIA_PRESHARED_KEY,
        ip="10.0.0.2",
        dns=["1.1.1.1", "8.8.8.8"],
        mtu=1420,
        jc=3,
        jmin=50,
        jmax=1000,
        s1=55,
        s2=110,
        h1=123456789,
        h2=987654321,
        h3=112233445,
    )
