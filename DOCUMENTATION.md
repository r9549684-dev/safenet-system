# SafeNet VPN — Документация проекта

SafeNet VPN — кроссплатформенное приложение (Flutter) + бэкенд (FastAPI). VPN-сервис с AmneziaWG/WireGuard, VLESS+Reality (Xray), системой подписок, промокодов и партнёрской программой.

---

## 📂 Структура репозитория

```
C:\safenet_vpn\
├── backend/
│   ├── app/
│   │   ├── api/          # Роутеры: auth, users, vpn, payments, affiliate, promocodes, servers, profiles, support, version
│   │   ├── models/       # SQLAlchemy ORM-модели (см. ниже)
│   │   ├── schemas/      # Pydantic-схемы
│   │   ├── services/     # Бизнес-логика: wireguard, xray, cryptobot, affiliate, entitlements
│   │   ├── utils/        # security, idempotency
│   │   ├── config.py     # Settings (pydantic-settings, .env)
│   │   └── main.py
│   ├── alembic/versions/ # Миграции: 0001_init → 0002 → 0003 → 0004
│   └── requirements.txt
├── infra/
│   ├── docker-compose.yml
│   ├── Caddyfile
│   └── .env              # Продакшн-конфигурация
├── lib/
│   ├── screens/          # Экраны: home, servers, affiliate, support, onboarding…
│   ├── providers/        # State management (Provider)
│   ├── services/         # update_checker.dart, …
│   └── l10n/             # Сгенерированные файлы локализации
├── android/              # Нативный Kotlin (AmneziaWG, ByeDPI, Xray)
└── pubspec.yaml
```

---

## 🗄 Модели БД (SQLAlchemy)

### `User` — `models/user.py`
Основная сущность. Подписка хранится полями в самой модели (нет отдельной таблицы Subscription).

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID PK | |
| `device_id` | String, unique | Идентификатор устройства |
| `country` | String(2) | Страна пользователя |
| `referral_code` | String(16), unique | Личный реф-код |
| `referred_by` | UUID FK | Кто привёл |
| `is_premium` | Boolean | Активная подписка |
| `premium_until` | DateTime | До какого времени |
| `trial_ends_at` | DateTime | Конец пробного периода |
| `created_at` | DateTime | |
| `ton_wallet` | String(64) | TON-кошелёк партнёра |
| `user_type` | String(16) | `regular` / `partner` |
| `referral_balance` | Numeric(18,6) | Баланс в TON |
| `paid_referrals_count` | Integer | Кол-во оплативших рефералов |
| `next_payment_discount` | Numeric(5,2) | Скидка на следующий платёж (0–50%) |

Вычисляемые свойства: `is_trial`, `is_partner`, `affiliate_rate`.

### `Invoice` — `models/invoice.py`
Инвойсы CryptoBot.

| Поле | Описание |
|---|---|
| `provider_invoice_id` | ID инвойса у провайдера (unique) |
| `asset` | Валюта (USDT, TON…) |
| `amount` | Сумма |
| `status` | `active` / `paid` / `expired` |
| `payload` | Строка `user:{id}:months:{n}` |
| `paid_at` | Время оплаты |

### `Server` — `models/server.py`
| Поле | Описание |
|---|---|
| `country` | Код страны (RU, TR, AE…) |
| `host` | IP/домен сервера |
| `port` | WireGuard UDP-порт (default 51820) |
| `is_active` | Активен ли сервер |
| `priority` | Приоритет при выборе |
| `meta` | JSON: публичный ключ WireGuard, тип узла |

### `Profile` — `models/profile.py`
Конфиги ByeDPI и AmneziaWG по странам (заполняется через `seed.py`).

| Поле | Описание |
|---|---|
| `country` | Код страны (unique) |
| `version` | Версия конфига |
| `payload` | JSON: режимы, параметры ByeDPI/AmneziaWG, fallback |

### `UserConnection` — `models/connection.py`
Активные WireGuard-соединения (уникальная пара user+server).

| Поле | Описание |
|---|---|
| `user_id` / `server_id` | FK |
| `peer_private_key` | WG-ключ клиента (plaintext, MVP) |
| `peer_public_key` | WG публичный ключ |
| `allocated_ip` | Выделенный IP из пула 10.8.0.2–254 |
| `is_active` | Статус соединения |
| `last_used_at` | Последнее использование |

### `ReferralTransaction` — `models/affiliate.py`
Транзакции реф-программы.

| Поле | Описание |
|---|---|
| `transaction_type` | `cpa` / `revshare` / `revshare_zero` / `discount` |
| `amount_ton` | Сумма в TON |
| `invoice_id` | Привязка к инвойсу (idempotency) |
| `status` | `pending` / `completed` |

### `WithdrawalRequest` — `models/affiliate.py`
Заявки на вывод средств партнёрами.

| Поле | Описание |
|---|---|
| `amount_ton` | Сумма вывода |
| `ton_wallet` | Адрес назначения |
| `status` | `pending` / `processing` / `completed` / `rejected` |

### `PromoCode` — `models/promocode.py` *(добавлено 24.02.2026)*

| Поле | Описание |
|---|---|
| `code` | Уникальный код (uppercase) |
| `kind` | `1m` / `3m` / `12m` |
| `duration_months` | 1 / 3 / 12 |
| `max_uses` | Лимит использований (default 1 — одноразовый) |
| `used_count` | Сколько раз активирован |
| `is_revoked` | Отозван ли |
| `expires_at` | Срок действия (nullable) |

### `PromoCodeRedemption` — `models/promocode.py`
Аудит активаций промокодов. Уникальный индекс `(promo_code_id, user_id)` — один юзер не активирует код дважды.

---

## 🌐 API Эндпоинты

### Auth `POST /auth/device`
Регистрация/логин по `device_id`. Возвращает JWT (30 дней).

### Users
- `GET /users/me` — профиль текущего пользователя

### VPN
- `POST /vpn/connect/{server_id}` — выдаёт WireGuard-конфиг + ByeDPI-профиль + VLESS-конфиг. Проверяет доступ (trial/premium). Выделяет IP, регистрирует пир, применяет лимит скорости (`trial=3Mbit`, `premium=10Mbit`).

### Payments (CryptoBot)
- `POST /payments/cryptobot/invoice` — создать инвойс
- `POST /payments/cryptobot/webhook` — обработать событие оплаты → выдаёт premium, начисляет реф-вознаграждение

### Servers & Profiles
- `GET /servers` — список активных серверов
- `GET /profiles` — ByeDPI/AmneziaWG конфиги по стране

### Affiliate (реф-программа)
- `GET /affiliate/profile` — баланс, статистика, минимум вывода
- `POST /affiliate/wallet` — привязать TON-кошелёк
- `POST /affiliate/apply-partner` — стать партнёром
- `POST /affiliate/withdraw` — запрос на вывод (мин. ~$5 в TON)
- `GET /affiliate/withdrawals` — история выплат
- `GET /affiliate/transactions` — история начислений
- `GET /affiliate/admin/withdrawals` *(X-Admin-Secret)* — pending-заявки
- `POST /affiliate/admin/withdrawals/{id}/approve` *(X-Admin-Secret)*
- `POST /affiliate/admin/withdrawals/{id}/reject` *(X-Admin-Secret)*

### Промокоды *(добавлено 24.02.2026)*
- `POST /promocodes/admin/create` *(X-Admin-Secret)* — создать промокод (`kind`, `code?`, `expires_at?`)
- `GET /promocodes/admin/list` *(X-Admin-Secret)* — список всех промокодов
- `POST /promocodes/admin/{code}/revoke` *(X-Admin-Secret)* — отозвать
- `POST /promocodes/redeem` *(Bearer JWT)* — активировать промокод → выдаёт premium

### Версия приложения *(добавлено 25.02.2026)*
- `GET /app/version` *(публичный)* — текущая версия APK для in-app чекера обновлений

**Поля ответа:**
```json
{ "version": "1.0.0", "version_code": 1, "force_update": false,
  "download_url": "http://89.208.107.67:8500/static/safenet-latest.apk",
  "changelog": "..." }
```
Чтобы принудить пользователей обновиться: поднять `version_code` в `backend/app/api/version.py` и установить `force_update=True`, затем пересобрать API-контейнер.

---

## 🤝 Партнёрская программа

Логика: `app/services/affiliate.py`

- **CPA (First Deposit):** $1.5 в TON за первую оплату реферала
- **RevShare (Recurring):** % от суммы последующих продлений

Уровни RevShare (по кол-ву оплативших рефералов):
- 1–100: 0% (только CPA)
- 101–500: 10%
- 501–1000: 15%
- 1001–1500: 20%
- 1500+: 25%

Обычный пользователь (не партнёр) — получает 50% скидку на следующий платёж за оплатившего реферала.
Вывод: минимум ~$5 в TON через CryptoBot Transfer API. Курс TON/USD — CoinGecko (fallback 3.0).

---

## 🎟 Система промокодов

Типы: `1m` (1 месяц), `3m` (3 месяца), `12m` (12 месяцев).
Код одноразовый (`max_uses=1`). Повторная активация одним пользователем блокируется на уровне БД (unique constraint).
Админ создаёт/отзывает коды через эндпоинты с `X-Admin-Secret`.

---

## 🔐 Авторизация

- **Пользовательские эндпоинты:** Bearer JWT (HS256, 30 дней)
- **Админские эндпоинты:** Заголовок `X-Admin-Secret: <ADMIN_SECRET из .env>`
- Текущий `ADMIN_SECRET` на сервере: `safenet_admin_2026`

---

## 🏗 Инфраструктура (Сервер 89.208.107.67)

### Docker-контейнеры
- `infra-api-1` — FastAPI (порт 8000 внутри, 8500 наружу)
- `infra-db-1` — PostgreSQL 15 (только внутри сети)
- `infra-caddy-1` — Caddy (80/443, SSL для `api.loveaibot.net`)

### WireGuard
- Интерфейс: `wg0`, пул: `10.8.0.1/24`, порт: `51820/UDP`
- Управление пирами: `wg-manager.py` (systemd, `172.18.0.1:9876`)
- Лимиты скорости: trial → 3 Мбит/с, premium → 10 Мбит/с (tc htb)

### Xray (VLESS+Reality)
- Порт: `2053/TCP`, dest: `www.microsoft.com:443`
- UUID, PublicKey, ShortId — в `.env` и `/etc/xray/reality-keys.txt`

### Миграции Alembic
- `0001_init` — базовые таблицы
- `0002_add_user_connections` — таблица `user_connections`
- `0003_add_affiliate_system` — affiliate-поля в `users`, `referral_transactions`, `withdrawal_requests`
- `0004_add_promocodes` — таблицы `promo_codes`, `promo_code_redemptions` *(24.02.2026)*
- `0005_add_support` — таблицы `support_sessions`, `support_messages` *(25.02.2026)*

---

## 📱 Мобильное приложение (Flutter / Android)

- **Auth:** Device ID (без пароля)
- **VPN:** AmneziaWG (основной) + VLESS+Reality (fallback)
- **ByeDPI:** SOCKS5-прокси для обхода DPI (foreground service)
- **Payments:** CryptoBot Web URL
- **Affiliate:** реферальная ссылка, QR-код, статистика
- **Доступ:**
  - Trial: 3 дня полного доступа (после — 403)
  - Premium: полный доступ (10 Мбит/с)
- Зависимость: `libs/amneziawg.aar` (нативная библиотека)

### 🏠 Редизайн главного экрана *(добавлено 25.02.2026)*

Карточка выбора сервера убрана с главного экрана и перенесена в раздел **Настройки** (секция «VPN Profile»).
На главном экране теперь два блока:

**Block A — Партнёрский баннер:**
Градиентная карточка `💰 Зарабатывай с SafeNet` (цвета `#4F46E5 → #7C3AED`). Нажатие открывает `AffiliateScreen`.

**Block B — Реферальный QR:**
Показывает QR-код реферальной ссылки пользователя + текстовый код + кнопку копирования. Данные подгружаются через `AffiliateProvider.loadProfile()` при старте экрана.

**Карточка сервера в Настройках:**
`Consumer<VpnProvider>` → `GestureDetector` → `ServersScreen`. Показывает флаг страны, название, пинг выбранного сервера.

---

### 🔄 Переименование режимов Bypass *(добавлено 25.02.2026)*

Отображаемые названия режимов изменены во всех трёх языках (ARB-файлы):

| Внутреннее имя | EN | RU | FA |
|---|---|---|---|
| `stealth` → `auto` | Auto | Авто | خودکار |
| `byedpi` → `bypass` | Bypass | Обход | دور زدن |
| `amneziawg` → `tunnel` | Tunnel | Туннель | تونل |
| `hybrid` → `maximum` | Maximum | Максимум | حداکثر |

FARB-ключи: `bypassModeAuto`, `bypassModeBypass`, `bypassModeTunnel`, `bypassModeMaximum`.
После правки ARB запустить: `flutter gen-l10n`.

---

### 📲 In-app чекер обновлений *(добавлено 25.02.2026)*

Файл: `lib/services/update_checker.dart`

При каждом запуске приложения (`initState` главного экрана) вызывается `UpdateChecker.check(context)`, который:
1. Делает `GET /app/version`
2. Сравнивает `version_code` с `PackageInfo.buildNumber`
3. Если сервер новее — показывает `AlertDialog` с градиентной кнопкой «Обновить» (открывает `download_url` через `url_launcher`) и кнопкой «Позже»
4. При `force_update=true` — кнопка «Позже» скрыта
5. Ошибки сети игнорируются (silent fail)

ARB-ключи для диалога: `updateTitle`, `updateMsg` (с плейсхолдером `{version}`), `updateBtn`, `updateLater`.

---

### 🌍 Локализация (добавлено 25.02.2026)

Приложение поддерживает 3 языка с полноценным RTL для фарси:

| Код | Язык | Шрифт | Направление |
|-----|------|-------|-------------|
| `en` | English | SF Pro Display | LTR |
| `ru` | Русский | SF Pro Display | LTR |
| `fa` | فارسی | Vazirmatn | **RTL** |

**Структура l10n:**
- ARB-файлы: `lib/l10n/app_en.arb`, `app_ru.arb`, `app_fa.arb` (~164 ключа)
- Сгенерированный код: `lib/l10n/app_localizations.dart` + `_en`, `_ru`, `_fa`
- Шрифт Vazirmatn: `assets/fonts/Vazirmatn-Regular.ttf`, `Vazirmatn-Bold.ttf`
- `l10n.yaml`: `arb-dir: lib/l10n`, `output-localization-file: app_localizations.dart`

**Выбор языка:**
Пользователь выбирает язык на экране онбординга (или в настройках). Выбор сохраняется в `SecureStorage` (ключ `language`, `flutter_secure_storage` — EncryptedSharedPreferences). **В БД поле `language` отсутствует** — хранится только локально на устройстве.

**Тема с учётом локали:**
`AppTheme.forLocale(locale)` в `lib/core/theme.dart` — для `fa`/`ar` применяет шрифт Vazirmatn, для остальных — SF Pro Display. Делегаты: `AppLocalizations.delegate`, `GlobalMaterialLocalizations`, `GlobalWidgetsLocalizations` (RTL layout).

**Обновление строк:**
```bash
flutter gen-l10n   # regenerate lib/l10n/ из ARB-файлов
```

**Сборка APK:**
```bash
flutter build apk --release
# → build/app/outputs/flutter-apk/app-release.apk
```
**Установка на устройство:**
```bash
adb install -r build/app/outputs/flutter-apk/app-release.apk
```

---

## 🌍 Деплой

**Сервер:** `89.208.107.67` | **Путь:** `/opt/safenet-v2`

**Обновление файлов (рекомендуемый способ — pscp/plink из PuTTY):**
```powershell
$p='C:\Program Files (x86)\PuTTY'; $srv='89.208.107.67'
# Загрузить файл на сервер
& "$p\pscp.exe" -pw $pw -batch file.py "root@${srv}:/opt/safenet-v2/backend/app/..."
# Скопировать в контейнер + миграция + рестарт
& "$p\plink.exe" -ssh -pw $pw -batch "root@$srv" @'
  docker cp /opt/safenet-v2/backend/app/... infra-api-1:/app/app/...
  cd /opt/safenet-v2/infra && docker compose exec -T api alembic upgrade head
  docker compose restart api
'@
```

**Полезные команды на сервере:**
```bash
docker logs -f infra-api-1          # логи API
docker compose ps                   # статус контейнеров
systemctl status xray               # статус Xray
systemctl status wg-manager         # статус wg-manager
wg show wg0                         # WireGuard пиры
```

---

## 🤖 Support API (добавлено 25.02.2026)

### Архитектура

AI-агент работает на Android-телефоне (Termux + Python + GLM-5 API). Flutter обращается к агенту напрямую через Cloudflare Tunnel. Агент использует **JWT пользователя** для всех вызовов — отдельный токен не нужен.

```
Flutter → [Cloudflare Tunnel → телефон (Termux + Python)]
                      ↓ JWT
         https://api.loveaibot.net/support/*
         GET /users/me  (контекст: premium/trial/partner)
```

### Таблицы (миграция `0005_add_support`)

**`support_sessions`** — один диалог = одна сессия:

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | |
| `lang` | VARCHAR(5) | `en` / `ru` / `fa` |
| `created_at` | TIMESTAMP | |
| `resolved_at` | TIMESTAMP, nullable | NULL = сессия открыта |
| `rating` | SMALLINT, nullable | 1–5, заполняет пользователь |

**`support_messages`** — сообщения внутри сессии:

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID PK | |
| `session_id` | UUID FK → support_sessions | |
| `user_id` | UUID FK → users | |
| `role` | VARCHAR(10) | `user` / `agent` |
| `message` | TEXT | |
| `created_at` | TIMESTAMP | |

Индексы: `support_sessions.user_id`, `support_sessions.resolved_at`, `support_messages.session_id`, `support_messages.user_id`.

### Эндпоинты `/support/*` (Bearer JWT)

| Метод | Путь | Кто | Что делает |
|---|---|---|---|
| `GET` | `/support/sessions/active?lang=ru` | Flutter | Активная сессия или авто-создание |
| `POST` | `/support/sessions` | Flutter | Явное создание сессии |
| `POST` | `/support/messages` | Агент | Сохранить сообщение (`role: user|agent`) |
| `GET` | `/support/history?session_id=&limit=50` | Агент | История сообщений сессии |
| `POST` | `/support/sessions/{id}/resolve` | Агент | Закрыть сессию |
| `POST` | `/support/sessions/{id}/rate` | Flutter | Оценка 1–5 |

**Нюанс:** `GET /sessions/active` — единственный вызов Flutter при открытии чата. Агент сохраняет оба сообщения: `role=user` → `role=agent` за один оборот.

### Cloudflare Tunnel (телефон агента)

```bash
# Termux:
pkg install cloudflared
cloudflared tunnel login
cloudflared tunnel create support-agent
cloudflared tunnel run support-agent
# → статичный URL прописывается в Flutter-конфиг
```

---

## 🛠 Контакты и доступы
- **GitHub:** https://github.com/r9549684-dev/safenet-vpn (Private)
- **API (prod):** https://api.loveaibot.net
- **API (direct):** http://89.208.107.67:8500
- **Разработчик:** Warp Agent
