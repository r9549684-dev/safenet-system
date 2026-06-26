from fastapi import APIRouter, HTTPException
from app.services.xray import get_vless_config, get_trojan_config
from app.services.regional_profiles import get_regional_profile

router = APIRouter(prefix="/api/v1/config", tags=["config"])


@router.get("/vless/{region}")
async def get_vless_config_endpoint(region: str):
    """Получить VLESS+Reality+Fragment конфиг для региона."""
    try:
        profile = get_regional_profile(region.upper())
        config = get_vless_config(profile)
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/trojan/{region}")
async def get_trojan_config_endpoint(region: str):
    """Получить Trojan+TLS конфиг для региона."""
    try:
        profile = get_regional_profile(region.upper())
        config = get_trojan_config(profile)
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
