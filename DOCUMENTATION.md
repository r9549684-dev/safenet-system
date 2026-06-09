# SafeNet service — Документация проекта

SafeNet service — кроссплатформенное приложение (Flutter) + бэкенд (FastAPI). service-сервис с AmneziaWG/WireGuard, VLESS+Reality (Xray), системой подписок, промокодов и партнёрской программой.

---

## 📂 Структура репозитория

```
C:\Users\53\Projects\SafeService\
├── backend/
│   ├── app/
│   │   ├── api/          # auth, users, service, payments, subscriptions, affiliate,
│   │   │                #  promocodes, servers, profiles, support, admin, version
│   │   ├── models/       # SQLAlchemy ORM-модели
│   │   ├── schemas/      # Pydantic-схемы
│   │   ├── services/     # wireguard, xray, cryptobot, affiliate, entitlements
│   │   ├── utils/        # security, idempotency
│   │   ├── config.py     # Settings (pydantic-settings, .env)
│   │   └── main.py
│   ├── alembic/versions/ # Миграции: 0001→0005
│   └── requirements.txt
├── infra/
│   ├── docker-compose.yml
│   ├── Caddyfile
│   ├── .env              # Продакшн-конфигурация
│   └── .env.example      # Шаблон (ADMIN_SECRET, AGENT_SECRET, …)
├── lib/
│   ├── core/
│   │   ├── config_cache_service.dart  # Очередь 3 слота + WG-кэш
│   │   ├── singbox_vpn.dart           # sing-box: fetch/failover/consumeAndRefresh
│   │   ├── pricing_service.dart       # Гео-цены из /subscriptions/pricing
│   │   ├── hiddify_installer.dart     # Распаковка sing-box бинарника
│   │   └── constants.dart
│   ├── screens/          # home, servers, affiliate, support, onboarding…
│   ├── providers/        # vpn_provider.dart, auth_provider.dart, subscription_provider.dart
│   ├── services/         # update_checker.dart
│   └── l10n/             # ARB + сгенерированные файлы (en/ru/fa)
├── android/
│   └── app/src/main/kotlin/com/safenet/service/
│       ├── MainActivity.kt
│       └── SingboxVpnService.kt       # Foreground service для sing-box
├── assets/
│   ├── singbox/          # sing-box-arm64, tun2socks-arm64
│   └── hiddify/          # hiddify.apk (резерв)
├── build_standard.ps1    # Сборка стандартного APK
├── build_iran.ps1        # Сборка APK для Ирана (bundleSingbox=true, country=IR)
├── build_china.ps1       # Сборка APK для ОАЭ/Китай (bundleSingbox=true, country=AE)
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
| `port` | WireGuard UDP-порт (443 UDP — изменён с 51820 25.02.2026) |
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

### service
- `POST /service/connect/{server_id}` — выдаёт WireGuard-конфиг + ByeDPI-профиль + VLESS-конфиг. Проверяет доступ (trial/premium). Выделяет IP, регистрирует пир, применяет лимит скорости (`trial=3Mbit`, `premium=10Mbit`).

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
- `POST /promocodes/admin/create` *(X-Admin-Secret)* — создать промокод
- `GET /promocodes/admin/list` *(X-Admin-Secret)* — список всех промокодов
- `POST /promocodes/admin/{code}/revoke` *(X-Admin-Secret)* — отозвать
- `POST /promocodes/redeem` *(Bearer JWT)* — активировать → выдаёт premium

### Версия приложения *(добавлено 25.02.2026)*
- `GET /app/version` *(публичный)* — текущая версия APK для in-app чекера обновлений

**Поля ответа:**
```json
{ "version": "1.0.0", "version_code": 1, "force_update": false,
  "download_url": "http://89.208.107.67:8500/static/safenet-latest.apk",
  "changelog": "..." }
```
Чтобы принудить обновить: поднять `version_code` в `backend/app/api/version.py`, `force_update=True`, пересобрать образ.

### Подписки с гео-ценами *(обновлено 05.03.2026)*
- `GET /subscriptions/pricing` — глобальные цены (обратная совместимость)
- `GET /subscriptions/pricing?country=AE` — цены для ОАЭ в USD + AED
- `GET /subscriptions/pricing?country=TR` — цены для Турции в USD + TRY
- `POST /subscriptions/purchase/{plan}?country=AE` — инвойс по гео-цене

**Цены ОАЭ (geo_mult 1.6678):**
| Тариф | USD | AED |
|---|---|---|
| weekly | $4.99 | ~18 |
| monthly | $9.99 | ~37 |
| quarterly | $24.99 | ~92 |
| yearly | $49.99 | ~183 |

**Глобальные цены:**
| Тариф | USD |
|---|---|
| weekly | $2.99 |
| monthly | $5.99 |
| quarterly | $14.99 |
| yearly | $29.99 |

### Telegram Link-Token *(добавлено 05.03.2026)*
- `POST /users/telegram-link-token` *(Bearer JWT)* — генерирует 6-симв. токен (TTL 10 мин), возвращает `{token, bot_url, expires_at}`
- `POST /users/link-telegram` *(X-Admin-Secret)* — `{token, telegram_id}` → связывает telegram_id с аккаунтом, очищает токен

**Сценарий:** Flutter-кнопка "🔗 Привязать Telegram" → `POST /users/telegram-link-token` → открывает `https://t.me/SafeBypass_bot?start={token}` → бот вызывает `POST /users/link-telegram` → аккаунты связаны.

### Admin API *(добавлено 05.03.2026)* — X-Admin-Secret: <ADMIN_SECRET>
- `GET /admin/stats` — дашборд: total/trial_active/premium/expired по странам + revenue (из CryptoBot API, не из БД)
- `GET /admin/users?status=trial_active|premium|expired&country=AE&page=1` — список с пагинацией
- `GET /admin/users/lookup?device_id=<UUID>` — полная карточка: статус, days_left, последние 10 инвойсов, последние 5 подключений
- `GET /admin/users/by-telegram?tg_id=<ID>` *(добавлено 05.03.2026)* — карточка пользователя по telegram_id

### Payments Admin API *(добавлено 05.03.2026)* — X-Admin-Secret: <ADMIN_SECRET>
- `POST /payments/admin/create-invoice` — создать CryptoBot-инвойс от имени бота
  - Body: `{"tg_id": 123456789, "plan": "monthly", "country": "AE"}` (или `device_id` вместо `tg_id`)
  - Ответ: `{invoice_id, pay_url, amount_usd, amount_local, currency, expires_at}`

**Назначение:** бот `@SafeBypass_bot` использует эти эндпоинты для создания инвойса без JWT.

### Revenue в /admin/stats *(обновлено 14.03.2026)*
Раздел `revenue` теперь берётся **напрямую из CryptoBot API** (не из локальной БД), чтобы Felix/SEIFY/бот, читающие из БД, не влияли на финансовые показатели:
- `wallet_balance` — текущий баланс кошелька по валютам (`getBalance`)
- `total_received` — сумма всех реально оплаченных инвойсов (`getInvoices?status=paid`), даже если средства уже сняты
- `paid_invoices` — количество реально оплаченных инвойсов

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
- ⚠️ **Не коммитьте реальное значение!** Укажите в `.env.example`: `<ADMIN_SECRET>`

---

## 🏗 Инфраструктура (Сервер 89.208.107.67)

### Docker-контейнеры
- `infra-api-1` — FastAPI (порт 8000 внутри, 8500 наружу)
- `infra-db-1` — PostgreSQL 15 (только внутри сети)
- `infra-caddy-1` — Caddy (80/443, SSL для `api.loveaibot.net`)

### WireGuard
- Интерфейс: `wg0`, пул: `10.8.0.1/24`, порт: **`443/UDP`** (изменён с 51820, 25.02.2026 — операторы IR/AE/TR блокировали 51820)
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
- `0006_add_post_trial_limit` — ограничение сессий после триала
- `0007_add_telegram_link` — поля `telegram_id BIGINT unique`, `link_token VARCHAR(10)`, `link_token_expires DATETIME` в таблице `users` *(05.03.2026)*

### Переменные окружения (.env ключи)
| Ключ | Значение (prod) | Описание |
|---|---|---|
| `ADMIN_SECRET` | `<ADMIN_SECRET>` | X-Admin-Secret для /admin/* и /affiliate/admin/* |
| `AGENT_SECRET` | `<AGENT_SECRET>` | X-Agent-Secret для POST /support/agent-message (Felix) |
| `CRYPTOBOT_TOKEN` | (в .env) | Токен CryptoBot |
| `SECRET_KEY` | (в .env) | JWT signing key |
| `TRIAL_DAYS` | `3` | Длительность триала |
| `TELEGRAM_BOT_USERNAME` | `SafeBypass_bot` | Username бота (без @) для link-token URL |

---

## 📱 Мобильное приложение (Flutter / Android)

- **Auth:** Device ID (без пароля)
- **service:** 3 режима (см. ниже)
- **Payments:** CryptoBot Web URL (гео-цены)
- **Affiliate:** реферальная ссылка, QR-код, статистика
- **Доступ:**
  - Trial: 7 дней (после — 403)
  - Premium: полный доступ (10 Мбит/с)

### Режимы service (кнопки на главном экране)

| Кнопка | Внутреннее | Протокол | Файл |
|---|---|---|---|
| **Максимальный режим** | `maximum` / hybrid | VLESS+Reality+Fragment (sing-box) | `singbox_vpn.dart` |
| **Тунель** | `tunnel` / amnezia | AmneziaWG / WireGuard | `vpn_provider.dart` |
| **Супер** | `super` / byedpi | ByeDPI SOCKS5 + WireGuard | `vpn_provider.dart` |

### Sing-box (Максимальный режим) *(добавлено 03.03.2026)*

`lib/core/singbox_vpn.dart` + `SingboxVpnService.kt` (foreground service)

**Флаг сборки:** `const bundleSingbox = bool.fromEnvironment('BUNDLE_HIDDIFY', defaultValue: false)`  
Если `true` — использует bundled бинарник (`assets/singbox/sing-box-arm64`).

**Жизненный цикл:**
1. `fetchConfig(token, country)` — берёт конфиг из головы очереди (`dequeue`) или из сети
2. `start(config)` → если `false` — failover: берёт следующий из очереди, повторная попытка
3. После успешного старта: `consumeAndRefreshCache(token, country)` — fire-and-forget фоновое пополнение

### Горячий запас конфигов *(добавлено 03.03.2026)*

`lib/core/config_cache_service.dart`

**Очередь 3 слота** (`spare_config_<COUNTRY>_0/1/2` в EncryptedSharedPreferences):
- `dequeue(country)` — взять из головы, сдвинуть очередь
- `enqueue(country, config)` — добавить в хвост
- `queueLength(country)` — количество живых слотов
- `preload(token, country)` — заполнить очередь до 3 при старте
- `consumeAndRefresh(token, country)` — уведомить сервер + фоново enqueue

**WG-кэш** (`wg_config_<serverId>`, TTL 48ч):
- `saveWgCache(serverId, wgConfig)` — после успешного WG-подключения
- `getWgCache(serverId)` — при падении сети (офлайн-подключение)

**Сценарии восстановления:**
| Ситуация | Время |
|---|---|
| Очередь есть | 0 мс |
| Очередь пуста | ~2 сек (API) |
| Sing-box упал, след. конфиг в очереди | ~1 сек (failover) |
| WG-сеть упала, кэш есть | 0 мс |

### Варианты APK

| Скрипт | Флаги | Назначение |
|---|---|---|
| `build_standard.ps1` | — | Стандартный (~29 МБ) |
| `build_iran.ps1` | `BUNDLE_HIDDIFY=true, country=IR` | Иран (~50 МБ, sing-box внутри) |
| `build_china.ps1` | `BUNDLE_HIDDIFY=true, country=AE` | ОАЭ/Китай (~50 МБ, sing-box внутри) |
- Зависимость: `libs/amneziawg.aar` (нативная библиотека)

### 🏠 Редизайн главного экрана *(добавлено 25.02.2026)*

Карточка выбора сервера убрана с главного экрана и перенесена в раздел **Настройки** (секция «service Profile»).
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

## 🤖 Техподдержка (обновлено 14.03.2026)

### Экран `SupportScreen` (`lib/screens/support_screen.dart`)

Открывается из вкладки **Настройки** — карточка `💬 Техподдержка / FAQ · AI-агент`.

**Карточки:**
- `✈️ Написать в поддержку через Telegram` — открывает `https://t.me/SafeBypass_bot`

- `❓ FAQ` — встроенная база знаний (15+ Q&A, ru/en/fa), `FaqScreen`
- `🤖 AI-агент SEIFY` — **встроенный AI-чат** прямо в приложении (`AiChatScreen`)

### Support API — Архитектура

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
| `POST` | `/support/ask` | Flutter (JWT) | **AI-ответ** — FAQ search, сохраняет оба сообщения |
| `POST` | `/support/messages` | Flutter (JWT) | Сохранить сообщение пользователя (role=user) |
| `POST` | `/support/agent-message` | Felix (X-Agent-Secret) | Ответ агента (role=agent автоматически) |
| `GET` | `/support/history?session_id=&limit=50` | Flutter | История сообщений сессии |
| `POST` | `/support/sessions/{id}/resolve` | Агент | Закрыть сессию |
| `POST` | `/support/sessions/{id}/rate` | Flutter | Оценка 1–5 |

**Аутентификация:**
- Пользователи (Flutter): `Authorization: Bearer <JWT>`
- Felix-бот: `X-Agent-Secret: safenet_agent_felix_2026`

**POST /support/ask — формат:**
```json
{"message": "Как оплатить?", "lang": "ru"}
// → {"answer": "...", "source": "faq", "topic": "payment"}
```

---

## 🌍 Рынки

### ОАЭ — основной рынок *(выбран 05.03.2026)*
- **Статус:** активен, приоритетный
- **Причина:** 65.78% service-проникновение, 88% экспатов, DPI-цензура (не BGP), высокая покупательная способность
- **Ценообразование:** $4.99/нед · $9.99/мес · $24.99/кварт · $49.99/год (geo_mult 1.6678)
- **Местная валюта:** AED (дирхам, fx_rate ~3.67)
- **Онбординг:** отдельный EN-флоу (build_china.ps1, country=AE, bundleSingbox=true)
- **Поддержка:** Felix в режиме EN + RAG-база по AE

### Иран — пауза
- **Статус:** приостановлен с 28.02.2026
- **Причина:** BGP-shutdown (операторы IR вырезаны из глобального интернета на BGP-уровне, ~1% связности). service не работает на BGP-уровне.
- **Технический стек для IR:** build_iran.ps1 (bundleSingbox=true, sing-box VLESS+Reality+Fragment) — готов к возобновлению при восстановлении связности
- **Мониторинг:** https://ioda.inetintel.cc.gatech.edu/

### Турция — планируется
- **Статус:** в бэкенде поддержан (geo_mult=0.8330, TRY)
- **Ценообразование:** рассчитывается автоматически по geo_mult
- **Старт:** после стабилизации ОАЭ

---

## 🤝 Felix — интеграция AI-поддержки *(обновлено 14.03.2026)*

- **Бот:** @SafeBypass_bot (Telegram, SEIFY AI + LightRAG + FAQ fallback)
- **Роль:** RAG-агент поддержки (отвечает на вопросы пользователей через Telegram + чат в приложении)
- **Токен:** `AGENT_SECRET=safenet_agent_felix_2026` (в `infra/.env`)
- **Эндпоинт ответа:** `POST /support/agent-message` (X-Agent-Secret)
- **Файл общения:** `C:\Users\53\Felix\Разработчики\Файл общения разработчиков сервис и техподд.md`
- **Локальный проект:** `C:\Users\53\Felix\`

### SEIFY AI — интеграция в Telegram-бот *(добавлено 14.03.2026)*

**Файлы:**
- `scripts/telegram_bot.py` — бот (aiogram 3) + SEIFY AI обработчик свободных сообщений
- `scripts/ai_agent.py` — SafeVPNAgent (TopicFilter, DialogueMemory, RAG, Admin API lookup, Account Card)
- `scripts/seify_uae_exam.py` — UAE-экзамен (теперь с реальным SEIFY Agent)

**Функции бота:**
- Команды: /start, /help, /pay, /download, /unlink + callback confirm/cancel link
- Свободные сообщения → SEIFY AI:
  - UUID в тексте → карточка аккаунта (`GET /admin/users/lookup`)
  - service-вопрос → RAG-поиск (LightRAG или FAQ keyword fallback)
  - Off-topic → блокировка с предложением service-тем
- Автоопределение языка: RU/EN/FA/TR/AR
- Feedback кнопки 👍/👎 для обучения

**FAQ база знаний (10 документов):**
- 7 FAQ по странам (IR/TR/AE на RU/EN/FA/TR/AR)
- 2 протокола (RU/EN)
- 1 General FAQ EN (новый 14.03.2026 — download, pricing, iOS, refund, multi-device, legality UAE, encryption, referral)

**Статус интеграции:**
| Шаг | Статус |
|---|---|
| `POST /support/agent-message` эндпоинт | ✅ готов |
| `AGENT_SECRET` передан Felix | ✅ передан |
| SEIFY AI интегрирован в бот | ✅ готово (14.03.2026) |
| FAQ база знаний (10 доков, 5 языков) | ✅ готово |
| Синтаксис бота исправлен (стр. 281) | ✅ исправлено |
| UAE-экзамен: реальный SEIFY Agent | ✅ готово |
| Локальный тест бота | ⏳ следующий шаг |
| Деплой бота на сервер | ⏳ после теста |
| Flutter UI чата (AiChatScreen) | ✅ готово (14.03.2026) |
|| /support/ask + ai_support.py | ✅ задеплоено (14.03.2026) |

---

## 🛠 Контакты и доступы
- **GitHub:** https://github.com/r9549684-dev/safenet-service (Private)
- **API (prod):** https://api.loveaibot.net
- **API (direct):** http://89.208.107.67:8500
- **Разработчик:** Warp Agent

---

## 📋 Changelog — сессия 13.03.2026

### ✅ Fix: device_id сбрасывался при переустановке приложения

**Проблема:** При удалении и повторной установке APK генерировался новый UUID → новый пользователь в БД → потеря подписки/промокода.

**Причина:** `FlutterSecureStorage` (EncryptedSharedPreferences) хранит данные в приватной директории приложения. Android **удаляет** их вместе с приложением при uninstall.

**Исправление:**
- `android/app/src/main/kotlin/com/safenet/service/MainActivity.kt` — добавлен обработчик `getAndroidId` в MethodChannel `com.safenet.service/methods`. Возвращает `Settings.Secure.ANDROID_ID` — аппаратный ID, который **не меняется при переустановке** (только при factory reset или смене пользователя Android).
- `lib/data/repositories/auth_repo.dart` — `getOrCreateDeviceId()` теперь:
  1. Проверяет сохранённый ID в SecureStorage (backward-compatible для существующих пользователей)
  2. Если нет → запрашивает `ANDROID_ID` через MethodChannel
  3. Fallback на random UUID (только если ANDROID_ID недоступен)

**Результат:** Переустановка приложения больше не создаёт новый аккаунт — пользователь получает тот же `device_id` и сохраняет подписку.

---

## 📋 Changelog — сессия 06.03.2026

### ✅ Fix: `subscriptions_router` не был зарегистрирован

**Проблема:** `POST /subscriptions/*` возвращал 404 для всех маршрутов.
**Причина:** `subscriptions_router` не был подключён в `backend/app/api/__init__.py` и `main.py`.
**Исправление:** Добавлен `include_router(subscriptions_router)` в оба файла.
**Деплой:** `docker cp` → `docker compose restart api`.

---

### ✅ Fix: CryptoBot `paid_btn_url` — неверное имя бота

**Файл:** `backend/app/services/cryptobot.py`
**Было:** `paid_btn_url` указывал на `LoveAIbot`
**Стало:** Исправлено на `SafeBypass_bot`

---

### ✅ USDT TRC20/TON — переименование метки

**Было:** `USDT / TON`
**Стало:** `USDT TRC20/TON`

Изменено в 7 файлах:
- `lib/screens/home_screen.dart` (строка 863)
- `lib/l10n/app_en.arb`, `app_ru.arb`, `app_fa.arb`
- `lib/l10n/app_localizations_en.dart`, `_ru.dart`, `_fa.dart`

**Релиз:** APK v1.2.0 загружен на GitHub Releases.
**Ссылка:** https://github.com/r9549684-dev/safenet-service/releases/download/v1.2.0/SafeNet-v1.2.0.apk

**Актуальный релиз:** APK v1.3.1
**Ссылка для скачивания (GitHub, приватный):** https://github.com/r9549684-dev/safenet-service/releases/download/v1.3.1/SafeNet-v1.3.1.apk
**Актуальная публичная ссылка:** https://api.loveaibot.net/download/app
**Версия на сервере (`GET /app/version`):** `{"version":"1.3.1","version_code":4}`

---

### ✅ Fix: VoIP дропы на WireGuard (Premium)

**Проблема:** Регулярные обрывы VoIP-звонков каждые ~2–3 минуты на премиум-аккаунтах.

**Причина 1 — частый рехендшейк WireGuard:**
`PersistentKeepalive` был 25 сек → слишком долго для NAT-таймаутов у сотовых операторов.

**Исправление 1:**
- Файл: `backend/app/services/wireguard.py`, строка 144
- Было: `PersistentKeepalive = 25`
- Стало: `PersistentKeepalive = 10`

**Причина 2 — `tc class del/add` при реконнекте разрывает пакеты:**
При переподключении активного пира `peer-limit.sh` пересоздавал TC-класс, вызывая кратковременный packet loss.

**Исправление 2:**
- Файл: `backend/app/api/service.py`
- Добавлен флаг `peer_was_active` (проверяет `is_active` до вызова connect)
- Если пир уже был активен — `apply_speed_limit` пропускается (TC не трогается)

**Деплой:** оба файла загружены через `docker cp`, `docker compose restart api`.

---

### ✅ Новый эндпоинт: `POST /users/unlink-telegram`

**Файл:** `backend/app/api/users.py` (строки 123–152)
**Аутентификация:** `X-Admin-Secret: <ADMIN_SECRET>`

**Тело запроса:**
```json
{"telegram_id": 123456789}
```

**Ответ (200 OK):**
```json
{"ok": true, "message": "Telegram unlinked", "device_id": "<uuid>"}
```

**Ответ (404):**
```json
{"detail": "User not found"}
```

**Логика:** Находит пользователя по `telegram_id`, устанавливает `telegram_id = None`, сохраняет в БД.

**Назначение:** Позволяет администратору (или боту Felix) отвязать Telegram-аккаунт от устройства — например, если пользователь сменил аккаунт или требует удаления данных (GDPR/Privacy).

---

### 📋 Рекомендации для бота по Privacy (GDPR)

Для Felix (@SafeBypass_bot) рекомендуется реализовать:

1. **Уведомление перед привязкой:** при команде `/link` или нажатии «Привязать» показывать текст:
   > «Привязывая Telegram, вы разрешаете SafeNet хранить ваш Telegram ID для управления подпиской. Вы можете отвязать его в любой момент командой /unlink.»
   С кнопками: **✅ Принять** | **❌ Отмена**

2. **Команда `/unlink`:** бот вызывает `POST /users/unlink-telegram` с `telegram_id` пользователя, подтверждает отвязку.

3. **Хранение только необходимых данных:** в БД хранится только `telegram_id` (integer), имя/username не сохраняются.
