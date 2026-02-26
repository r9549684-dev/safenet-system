from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["version"])


class AppVersionResponse(BaseModel):
    version: str
    version_code: int
    force_update: bool
    download_url: str
    changelog: str


# ─── Конфигурация текущей версии ────────────────────────────────────────────
# version_code должен совпадать с versionCode в Android build.gradle
# (pubspec.yaml: version: X.Y.Z+N, где N = version_code)
# Чтобы принудить обновление: поднять version_code и установить force_update=True
_CURRENT_VERSION = AppVersionResponse(
    version="1.0.0",
    version_code=1,
    force_update=False,
    download_url="http://89.208.107.67:8500/static/safenet-latest.apk",
    changelog="Партнёрская программа, QR реферальный код, обновлённый интерфейс",
)


@router.get("/app/version", response_model=AppVersionResponse)
def get_app_version() -> AppVersionResponse:
    """Публичный эндпоинт. Мобильное приложение сверяет version_code при запуске."""
    return _CURRENT_VERSION
