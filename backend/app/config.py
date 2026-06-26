from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_BASE_URL: str = "http://localhost"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://safenet:safenet@db:5432/safenet"

    SECRET_KEY: str = "CHANGE_ME"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    TRIAL_DAYS: int = 3

    CRYPTOBOT_TOKEN: str = ""
    CRYPTOBOT_SIGNATURE_HEADER: str = "Crypto-Pay-Signature"

    CORS_ORIGINS: str = ""

    # Xray / VLESS+Reality
    XRAY_UUID: str = ""
    XRAY_PUBLIC_KEY: str = ""
    XRAY_SHORT_ID: str = ""
    XRAY_PORT: int = 2053

    # Xray / Trojan+TLS
    TROJAN_PASSWORD: str = ""
    TROJAN_PORT: int = 4443

    # Admin secret for admin endpoints
    ADMIN_SECRET: str = ""
    # Agent secret for Felix bot (POST /support/agent-message)
    AGENT_SECRET: str = ""
    # Telegram bot username (without @) for link generation
    TELEGRAM_BOT_USERNAME: str = "SafeBypass_bot"

    def cors_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return []
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]

    class Config:
        env_file = ".env"


settings = Settings()
