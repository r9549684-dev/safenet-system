from app.config import settings
from app.services.xray_models import FragmentOpts, RealityOpts, VlessRealityParams


def get_vless_config(server_ip: str) -> VlessRealityParams:
    """Возвращает типизированный VLESS+Reality+Fragment конфиг для клиента.

    Контракт: всегда включает fragment (tlshello), security="reality",
    flow="xtls-rprx-vision". См. xray_models.VlessRealityParams.
    """
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
            server_name="www.microsoft.com",
            fingerprint="chrome",
        ),
        fragment=FragmentOpts(packets="tlshello"),
    )
