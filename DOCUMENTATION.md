# SafeNet VPN — Документация проекта

SafeNet VPN — это кроссплатформенное приложение (Flutter) с собственным бэкендом (FastAPI), реализующее VPN-сервис с обходом блокировок (Xray/VLESS) и партнерской программой.

## 📂 Структура репозитория

```
C:\safenet_vpn\
├── backend/             # Бэкенд на Python (FastAPI)
│   ├── app/
│   │   ├── api/         # Эндпоинты (VPN, Auth, Payments, Affiliate)
│   │   ├── models/      # SQLAlchemy модели (User, Invoice, etc.)
│   │   ├── services/    # Бизнес-логика (Xray, CryptoBot, Affiliate)
│   │   └── main.py      # Точка входа
│   ├── alembic/         # Миграции базы данных
│   └── docker-compose.yml
├── lib/                 # Исходный код Flutter приложения
│   ├── screens/         # UI экраны
│   ├── providers/       # State management (Provider)
│   ├── services/        # Локальные сервисы (VPN tunnel)
│   └── main.py          # Точка входа Flutter
├── android/             # Нативный код Android (Kotlin)
└── pubspec.yaml         # Зависимости Flutter
```

---

## 🚀 Бэкенд (Backend)

Бэкенд отвечает за авторизацию, управление подписками, интеграцию с Xray (VLESS) и CryptoBot, а также партнерскую программу.

### Установка и запуск (Docker)

1. **Окружение:** Создайте файл `.env` в папке `backend/` (пример в `.env.example`).
   Важные переменные:
   ```ini
   DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/safenet
   CRYPTOBOT_TOKEN=...
   ADMIN_SECRET=...
   XRAY_UUID=...
   ```

2. **Запуск:**
   ```bash
   cd backend
   docker compose up -d --build
   ```

3. **Миграции БД:**
   ```bash
   docker compose exec api alembic upgrade head
   ```

### 🤝 Партнерская программа (Affiliate System)

Логика начисления вознаграждений (`app/services/affiliate.py`):

1. **Типы начислений:**
   - **First Deposit (CPA):** За *первую* оплату реферала начисляется фикс **$1.5** (в TON).
   - **Recurring (RevShare):** За *последующие* оплаты (продление) начисляется **%** от суммы.

2. **Уровни партнеров (RevShare):**
   Процент зависит от количества *оплативших* рефералов:
   - 0–100: **0%** (только CPA)
   - 101–500: **10%**
   - 501–1000: **15%**
   - 1001–1500: **20%**
   - 1500+: **25%**

3. **Выплаты:**
   Партнеры запрашивают вывод средств на TON-кошелек через приложение. Заявки обрабатываются админом или автоматически (в коде есть `process_withdrawal`).

---

## 📱 Мобильное приложение (Flutter)

Приложение использует нативные плагины для управления VPN-туннелем (WireGuard/Xray).

### Сборка (Build)

**Android APK (Release):**
```bash
flutter build apk --release --no-tree-shake-icons
```
APK будет лежать в: `build/app/outputs/flutter-apk/app-release.apk`

### Ключевые функции
- **Auth:** Регистрация по Device ID (без пароля).
- **VPN:** Подключение к VLESS Reality (Xray).
- **Payments:** Оплата через CryptoBot (WebUrl).
- **Affiliate:** Экран статистики, реферальная ссылка, QR-код.
- **Доступ и ограничения:**
  - Первые **3 дня** — полный доступ как у Premium.
  - После окончания триала — сессии по **5 минут**.
  - `Kill Switch` защищает от утечки IP при обрыве VPN.

---

## 🌍 Деплой (Deployment)

**Сервер:** `89.208.107.67`
**Путь:** `/opt/safenet-v2`

**Обновление бэкенда:**
1. Загрузить обновленные файлы на сервер (через `scp` или `git pull`).
2. Перезапустить контейнер:
   ```bash
   ssh root@89.208.107.67 "cd /opt/safenet-v2/infra && docker compose up -d api"
   ```

**Полезные команды:**
*   Посмотреть логи: `docker logs -f infra-api-1`
*   Проверить статус Xray: `systemctl status xray`

---

## 🛠 Контакты и доступы
*   **GitHub:** https://github.com/r9549684-dev/safenet-vpn (Private)
*   **Разработчик:** Warp Agent
