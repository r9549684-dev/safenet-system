from .health import router as health_router
from .auth import router as auth_router
from .users import router as users_router
from .profiles import router as profiles_router
from .servers import router as servers_router
from .payments_cryptobot import router as payments_cryptobot_router
from .service import router as vpn_router
from .affiliate import router as affiliate_router
from .promocodes import router as promocodes_router
from .support import router as support_router
from .version import router as version_router
from .admin import router as admin_router
from .payments_admin import router as payments_admin_router
from .subscriptions import router as subscriptions_router
from .ano import router as ano_router

__all__ = [
    "health_router",
    "auth_router",
    "users_router",
    "profiles_router",
    "servers_router",
    "payments_cryptobot_router",
    "vpn_router",
    "affiliate_router",
    "promocodes_router",
    "support_router",
    "version_router",
    "admin_router",
    "payments_admin_router",
    "subscriptions_router",
    "ano_router",
]
