from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

router = APIRouter(tags=["version"])

APK_PATH = "/app/static/safenet-latest.apk"


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
    version="1.3.2",
    version_code=5,
    force_update=False,
    download_url="https://safenetsystem.duckdns.org/download/app",
    changelog="Fix: реферальные ссылки исправлены. QR-код и кнопка 'Копировать' теперь работают.",
)


@router.get("/app/version", response_model=AppVersionResponse)
def get_app_version() -> AppVersionResponse:
    """Публичный эндпоинт. Мобильное приложение сверяет version_code при запуске."""
    return _CURRENT_VERSION


@router.get("/download/app")
def download_app():
    """APK скачивание. Отдаёт файл с правильным MIME-типом и Content-Disposition."""
    if not os.path.exists(APK_PATH):
        raise HTTPException(status_code=404, detail="APK not found on server")
    return FileResponse(
        path=APK_PATH,
        media_type="application/vnd.android.package-archive",
        filename="SafeNet-latest.apk",
    )
