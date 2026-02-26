from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.logging_conf import setup_logging
from app.api import (
    health_router,
    auth_router,
    users_router,
    profiles_router,
    servers_router,
    payments_cryptobot_router,
    vpn_router,
    affiliate_router,
    promocodes_router,
    support_router,
    version_router,
)

setup_logging(settings.DEBUG)

app = FastAPI(title="SafeNet v2 MVP", debug=settings.DEBUG)

if settings.cors_list():
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(profiles_router)
app.include_router(servers_router)
app.include_router(payments_cryptobot_router)
app.include_router(vpn_router)
app.include_router(affiliate_router)
app.include_router(promocodes_router)
app.include_router(support_router)
app.include_router(version_router)
