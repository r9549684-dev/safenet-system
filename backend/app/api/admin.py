"""
Admin API — полная информация о клиентах для техподдержки.

Защита: X-Admin-Secret header == settings.ADMIN_SECRET

Endpoints:
  GET /admin/users/lookup   — карточка клиента по device_id
  GET /admin/users          — список клиентов с фильтрами
  GET /admin/stats          — дашборд: статистика по статусам и странам
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models.connection import UserConnection
from app.models.invoice import Invoice
from app.models.promocode import PromoCodeRedemption
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Auth ───────────────────────────────────────────────────────────────────────

def require_admin(x_admin_secret: Optional[str] = Header(default=None)):
    if not settings.ADMIN_SECRET or x_admin_secret != settings.ADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing admin secret",
        )


# ── Helpers ────────────────────────────────────────────────────────────────────

NOW = datetime.utcnow

def _status(user: User) -> str:
    """trial_active | premium | expired"""
    if user.is_premium:
        return "premium"
    if user.trial_ends_at and user.trial_ends_at > NOW():
        return "trial_active"
    return "expired"

def _user_card(user: User, premium_source: Optional[str] = None) -> dict:
    """Базовая карточка пользователя."""
    st = _status(user)
    days_left: Optional[int] = None
    if st == "premium" and user.premium_until:
        days_left = max(0, (user.premium_until - NOW()).days)
    elif st == "trial_active" and user.trial_ends_at:
        days_left = max(0, (user.trial_ends_at - NOW()).days)

    return {
        "device_id":    user.device_id,
        "country":      user.country,
        "status":       st,
        "is_premium":   user.is_premium,
        "premium_source": premium_source,  # "paid" | "promo" | None
        "premium_until": user.premium_until.isoformat() if user.premium_until else None,
        "days_left":    days_left,
        "trial_ends_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None,
        "user_type":    user.user_type,
        "paid_referrals_count": user.paid_referrals_count,
        "referral_balance": float(user.referral_balance),
        "next_payment_discount": float(user.next_payment_discount),
        "post_trial_connect_count": user.post_trial_connect_count,
        "account_created_at": user.created_at.isoformat(),
    }


# ── GET /admin/users/lookup ────────────────────────────────────────────────────

@router.get("/users/lookup", dependencies=[Depends(require_admin)])
async def lookup_user(
    device_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Полная карточка клиента по device_id.
    Включает: статус, подписка, триал, история платежей, последние подключения.
    """
    result = await session.execute(
        select(User).where(User.device_id == device_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(404, f"User '{device_id}' not found")

    # Последние 5 подключений
    conn_result = await session.execute(
        select(UserConnection)
        .where(UserConnection.user_id == user.id)
        .order_by(UserConnection.created_at.desc())
        .limit(5)
    )
    connections = conn_result.scalars().all()

    # Последние 10 платежей
    inv_result = await session.execute(
        select(Invoice)
        .where(Invoice.user_id == user.id)
        .order_by(Invoice.created_at.desc())
        .limit(10)
    )
    invoices = inv_result.scalars().all()

    card = _user_card(user)
    card["connections"] = [
        {
            "server_id":   c.server_id,
            "allocated_ip": c.allocated_ip,
            "is_active":   c.is_active,
            "last_used_at": c.last_used_at.isoformat() if c.last_used_at else None,
            "created_at":  c.created_at.isoformat(),
        }
        for c in connections
    ]
    card["invoices"] = [
        {
            "id":          inv.id,
            "plan":        inv.payload,
            "amount":      float(inv.amount),
            "asset":       inv.asset,
            "status":      inv.status,
            "paid_at":     inv.paid_at.isoformat() if inv.paid_at else None,
            "created_at":  inv.created_at.isoformat(),
        }
        for inv in invoices
    ]
    return card


# ── GET /admin/users ───────────────────────────────────────────────────────────

@router.get("/users", dependencies=[Depends(require_admin)])
async def list_users(
    status_filter: Optional[str] = Query(
        default=None,
        alias="status",
        description="trial_active | premium | expired",
    ),
    country: Optional[str] = Query(default=None, description="Код страны, напр. IR"),
    page:     int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    """
    Список клиентов с фильтрами по статусу и стране.

    status=trial_active  — только в триале
    status=premium       — только подписчики
    status=expired       — триал истёк, не платят
    country=IR           — только Иран (и т.д.)
    """
    now = NOW()
    q = select(User)

    # Фильтр по стране
    if country:
        q = q.where(User.country == country.upper())

    # Фильтр по статусу
    if status_filter == "premium":
        q = q.where(User.is_premium == True)  # noqa: E712
    elif status_filter == "trial_active":
        q = q.where(User.is_premium == False, User.trial_ends_at > now)  # noqa: E712
    elif status_filter == "expired":
        q = q.where(User.is_premium == False, User.trial_ends_at <= now)

    # Подсчёт total
    count_q = select(func.count()).select_from(q.subquery())
    total = (await session.execute(count_q)).scalar_one()

    # Пагинация
    q = q.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    users = (await session.execute(q)).scalars().all()

    # Определяем источник premium для каждого пользователя
    user_ids = [u.id for u in users if u.is_premium]
    promo_user_ids: set = set()
    paid_user_ids: set = set()
    if user_ids:
        promo_res = await session.execute(
            select(PromoCodeRedemption.user_id).where(PromoCodeRedemption.user_id.in_(user_ids))
        )
        promo_user_ids = {r for (r,) in promo_res.all()}
        paid_res = await session.execute(
            select(Invoice.user_id).where(Invoice.user_id.in_(user_ids), Invoice.status == "paid")
        )
        paid_user_ids = {r for (r,) in paid_res.all()}

    def _source(u: User) -> Optional[str]:
        if not u.is_premium:
            return None
        if u.id in paid_user_ids:
            return "paid"
        if u.id in promo_user_ids:
            return "promo"
        return "promo"  # premium без инвойса = промокод

    return {
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "pages":    max(1, (total + per_page - 1) // per_page),
        "users":    [_user_card(u, _source(u)) for u in users],
    }


# ── GET /admin/users/by-telegram ─────────────────────────────────────────

@router.get("/users/by-telegram", dependencies=[Depends(require_admin)])
async def get_user_by_telegram(
    tg_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Поиск пользователя по telegram_id.
    Используется @SafeBypass_bot для оплаты и проверки статуса.
    Если пользователь не привязал Telegram — 404,
    бот должен предложить привязать через SafeNet-приложение.
    """
    result = await session.execute(
        select(User).where(User.telegram_id == tg_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(404, "User not linked to this Telegram account")

    return _user_card(user)


# ── GET /admin/stats ───────────────────────────────────────────────

@router.get("/stats", dependencies=[Depends(require_admin)])
async def get_stats(
    session: AsyncSession = Depends(get_session),
):
    """
    Дашборд для техподдержки.

    Возвращает:
      - Общее кол-во пользователей
      - Разбивка по статусам (trial_active / premium / expired)
      - Разбивка по странам (с подстатусами)
      - Сумма платежей (всего paid инвойсов)
    """
    now = NOW()
    all_users = (await session.execute(select(User))).scalars().all()

    total       = len(all_users)
    trial_active = sum(1 for u in all_users if not u.is_premium and u.trial_ends_at and u.trial_ends_at > now)
    premium      = sum(1 for u in all_users if u.is_premium)
    expired      = sum(1 for u in all_users if not u.is_premium and (not u.trial_ends_at or u.trial_ends_at <= now))

    # Premium по источнику: paid vs promo
    premium_user_ids = [u.id for u in all_users if u.is_premium]
    paid_user_id_set: set = set()
    if premium_user_ids:
        paid_res = await session.execute(
            select(Invoice.user_id).where(
                Invoice.user_id.in_(premium_user_ids), Invoice.status == "paid"
            )
        )
        paid_user_id_set = {r for (r,) in paid_res.all()}
    premium_paid  = sum(1 for u in all_users if u.is_premium and u.id in paid_user_id_set)
    premium_promo = premium - premium_paid

    # По странам
    countries: dict = {}
    for u in all_users:
        c = u.country or "unknown"
        if c not in countries:
            countries[c] = {"total": 0, "trial_active": 0, "premium": 0, "expired": 0}
        countries[c]["total"] += 1
        countries[c][_status(u)] += 1

    # Revenue: реальные данные из CryptoBot API (не из локальной БД)
    # Обновлено 2026-03-14: безопасней — Felix/SEIFY/бот читают из БД, а stats берёт из кошелька
    import httpx
    cryptobot_balance: dict = {}
    cryptobot_paid_total = 0.0
    cryptobot_paid_count = 0
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            hdrs = {"Crypto-Pay-Api-Token": settings.CRYPTOBOT_TOKEN}
            # Баланс кошелька
            bal = (await http.get("https://pay.crypt.bot/api/getBalance", headers=hdrs)).json()
            if bal.get("ok"):
                for item in bal["result"]:
                    amt = float(item.get("available", 0))
                    if amt > 0:
                        cryptobot_balance[item["currency_code"]] = amt
            # Оплаченные инвойсы
            inv = (await http.get("https://pay.crypt.bot/api/getInvoices?status=paid", headers=hdrs)).json()
            if inv.get("ok"):
                for it in inv["result"].get("items", []):
                    cryptobot_paid_total += float(it.get("amount", 0))
                    cryptobot_paid_count += 1
    except Exception:
        pass

    return {
        "generated_at": now.isoformat(),
        "users_summary": {
            "total":        total,
            "trial_active": trial_active,
            "expired":      expired,
        },
        "paying_customers": {
            "total_premium": premium,
            "paid_subscribers": premium_paid,
            "promo_granted": premium_promo,
        },
        "revenue": {
            "wallet_balance":  cryptobot_balance if cryptobot_balance else {"USDT": 0, "TON": 0},
            "total_received":  round(cryptobot_paid_total, 2),
            "paid_invoices":   cryptobot_paid_count,
        },
        "by_country": dict(sorted(countries.items(), key=lambda x: -x[1]["total"])),
    }
