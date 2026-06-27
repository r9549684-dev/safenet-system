# Карта проекта SafeNet

**Дата обновления:** 2026-06-27  
**Статус:** ✅ Актуально

---

## Репозитории

| Репозиторий | Путь | Remote | Branch | Статус |
|-------------|------|--------|--------|--------|
| **safenet-system** | `D:\Felix\projects\safenet-system` | `git@github.com:r9549684-dev/safenet-system.git` | `master` | ✅ Основной (Flutter + Backend + Android) |
| **safenet-vps** | `D:\Felix\projects\safenet-vps` | `origin/master` (локальный) | `master` | ✅ Инфраструктура VPS |
| **isolated-browser** | `D:\Felix\projects\isolated-browser` | ❌ Нет remote | `wip-flutter` | ⚠️ Локальный (требует GitHub remote) |

---

## Единый источник правды

**`D:\Felix\projects\safenet-system`** — единственный репозиторий для:
- Flutter клиент (lib/)
- FastAPI backend (backend/)
- Android native (android/)
- Инфраструктура (infra/)
- Тесты (test/, backend/tests/)
- Сборка APK (build.ps1)

**GitHub:** https://github.com/r9549684-dev/safenet-system

---

## Junction-ссылки (D:\SafeNet)

| Junction | Target | Статус |
|----------|--------|--------|
| `D:\SafeNet\browser` | `D:\Felix\projects\isolated-browser` | ✅ Работает |
| `D:\SafeNet\memory` | `C:\Users\53\.qwen\projects\c--users-53\memory` | ✅ Работает |
| `D:\SafeNet\vps` | `D:\Felix\projects\safenet-vps` | ✅ Работает |
| `D:\SafeNet\vpn` | ~~`D:\Felix\projects\safenet-vpn`~~ | ❌ **УДАЛЁН** (target не существовал) |

**Примечание:** Junction `vpn` был удалён 2026-06-27. Target `safenet-vpn` был переименован в `safenet-system`.

---

## Серверы

| # | IP | Домен | Роль | Статус |
|---|-----|-------|------|--------|
| 1 | 38.180.253.219 | safenetsystem.duckdns.org | Master Node (All-in-One) | ✅ Active |
| 2 | 38.244.136.233 | systemsafenet.duckdns.org | Frontend Gateway | ✅ Active |

### SSH доступ
```powershell
# Server #1 (Master)
ssh -o IdentitiesOnly=yes -i C:\Users\53\.ssh\id_ed25519_felix root@38.180.253.219

# Server #2 (Gateway) — через jump host
ssh safenet2
```

---

## CI Workflows (safenet-system)

| Workflow | Файл | Назначение |
|----------|------|------------|
| Deploy Stealth | `.github/workflows/deploy-stealth.yml` | Деплой stealth-конфигов |
| Test SSH | `.github/workflows/test-ssh.yml` | Тест SSH подключения |
| VPS Relay S2 | `.github/workflows/vps-relay-s2.yml` | Relay для Server #2 |
| VPS Relay | `.github/workflows/vps-relay.yml` | Relay для Server #1 |

---

## Структура каталогов

```
D:\Felix\projects\
├── safenet-system\        ← ЕДИНСТВЕННЫЙ ИСТОЧНИК ПРАВДЫ
│   ├── lib\               ← Flutter клиент
│   ├── backend\           ← FastAPI backend
│   ├── android\           ← Android native (Kotlin)
│   ├── infra\             ← Docker Compose + Caddy
│   ├── test\              ← Flutter тесты
│   ├── build.ps1          ← ЕДИНСТВЕННЫЙ скрипт сборки
│   ├── BUILD.md           ← Инструкция по сборке
│   └── pubspec.yaml       ← Версия: 1.3.2+5
│
├── safenet-vps\           ← Инфраструктура VPS
│   ├── registry.md        ← Реестр серверов
│   ├── VLESS_MIGRATION_PLAN.md
│   ├── deploy_*.py        ← Скрипты деплоя
│   └── .env               ← Секреты (НЕ в git)
│
└── isolated-browser\      ← Isolated Browser (отдельный проект)
    ├── app\               ← Flutter приложение
    ├── transport-core\    ← Rust transport
    └── gateway\           ← Rust gateway

D:\SafeNet\                ← Навигационный хаб
├── browser\               ← junction → isolated-browser
├── memory\                ← junction → Qwen memory
├── vps\                   ← junction → safenet-vps
├── _audit\                ← Аудит (APK, diff, отчёты)
└── build_registry.csv     ← Реестр сборок APK

D:\Рефакторинг\            ← Рабочая директория рефакторинга
├── ANALYSIS_REPORT.md     ← Анализ проектов
└── TASK_FROM_REVIEWER.md  ← Задание от ревизора
```

---

## Протоколы (приоритет)

```
PRIMARY:   VLESS+Reality+Fragment (TCP 2053, SNI: microsoft.com)
FALLBACK1: Trojan+TLS (TCP 443, SNI: microsoft.com)
FALLBACK2: AmneziaWG (UDP 51821, stealth)
LEGACY:    WireGuard (UDP 51820)
```

---

## Ключевые файлы

| Файл | Путь | Описание |
|------|------|----------|
| BUILD.md | `safenet-system\BUILD.md` | Инструкция по сборке APK |
| PROJECT_MAP.md | `safenet-system\PROJECT_MAP.md` | Этот файл (карта проекта) |
| registry.md | `safenet-vps\registry.md` | Реестр серверов |
| CONTEXT_SPINE.md | `D:\SafeNet\CONTEXT_SPINE.md` | Активный контекст SafeNet |
| build_registry.csv | `D:\SafeNet\build_registry.csv` | Реестр сборок APK |

---

## Правила работы

1. **Сборка ТОЛЬКО через `build.ps1 -Flavor <name>`**
2. **Запрещено хардкодить IP/URL в коде** — только `--dart-define`
3. **Перед сборкой:** `git status` должен быть чист
4. **После сборки:** записать в `build_registry.csv`
5. **Запрещено создавать junction-ссылки** без записи в этом файле
6. **Untracked критичные файлы** коммитятся в тот же день
7. **При аномалии APK** (>30 MB для standard) — остановиться, расследовать

---

## Известные проблемы / TODO

### Критические

1. **isolated-browser — нет remote**
   - **Статус:** Локальный репозиторий
   - **Риск:** Потеря данных при сбое диска
   - **Решение:** Создать GitHub repo и привязать remote
   - **Команда:** `git remote add origin git@github.com:r9549684-dev/isolated-browser.git && git push -u origin wip-flutter`

2. **DuckDNS как дефолтный эндпоинт**
   - **Статус:** `https://safenetsystem.duckdns.org` захардкожен как defaultValue
   - **Риск:** DuckDNS легко блокируется цензорами (бесплатный dynamic-DNS)
   - **Решение:** Рассмотреть domain-fronting, несколько резервных эндпоинтов
   - **Временное решение:** Передавать через `--dart-define=API_BASE_URL=...`

### Важные

3. **safenet-vps — секреты в истории git**
   - **Статус:** Пароли удалены из текущих файлов, но могут быть в истории
   - **Решение:** `git filter-repo` для очистки истории
   - **Приоритет:** Высокий, если планируется публикация репо

4. **Fat APK с 3 ABI**
   - **Статус:** 48.79 MB (сжатый), 128.48 MB (uncompressed)
   - **Решение:** Split per ABI или только arm64-v8a
   - **Ожидаемый размер:** 15-20 MB для arm64 only

---

## Восстановление окружения с нуля

### 1. Ключи и секреты

**SSH ключи:**
- `C:\Users\53\.ssh\id_ed25519_felix` — доступ к Server #1
- `C:\Users\53\.ssh\id_ed25519_s1` — доступ к Server #2
- `C:\Users\53\.ssh\id_ed25519` — GitHub (r9549684-dev)

**Секреты SafeNet:**
- `D:\Felix\projects\safenet-vps\.env` — все пароли, ключи Xray, токены
- `D:\SafeNet\keys\.env` — дополнительные секреты

### 2. Flutter SDK

**Путь:** `C:\src\flutter` (v3.29.0, Dart 3.7.0)

**Установка:**
```powershell
# Скачать Flutter SDK
# https://docs.flutter.dev/get-started/install/windows

# Добавить в PATH
[System.Environment]::SetEnvironmentVariable('PATH', "$env:PATH;C:\src\flutter\bin", 'User')

# Проверка
flutter doctor
```

### 3. Ключи для сборки

**sing-box бинарники (для iran/china):**
- `assets\singbox\sing-box-arm64`
- `assets\singbox\tun2socks-arm64`

**Откуда получить:**
- Скачать из релизов: https://github.com/SagerNet/sing-box/releases
- Или скопировать из существующей сборки

### 4. Серверы

**Server #1 (Master):**
```powershell
ssh -o IdentitiesOnly=yes -i C:\Users\53\.ssh\id_ed25519_felix root@38.180.253.219
```

**Server #2 (Gateway):**
```powershell
ssh safenet2  # алиас в ~/.ssh/config
```

### 5. Переменные окружения

**Для отладки с прямым IP:**
```powershell
.\build.ps1 -Flavor standard -ApiUrl "http://38.180.253.219:8001"
```

**Для prod (по умолчанию):**
```powershell
.\build.ps1 -Flavor standard  # использует https://safenetsystem.duckdns.org
```

---

*Документ создан: 2026-06-27*  
*Автор: qwen/qwen3.7-plus (по заданию Claude Opus 4.8)*
