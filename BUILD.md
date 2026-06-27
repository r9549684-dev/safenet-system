# Сборка SafeNet

**Дата обновления:** 2026-06-27  
**Статус:** ✅ Актуально

---

## Единственный способ сборки

```powershell
.\build.ps1 -Flavor <standard|iran|china|debug> [-ApiUrl <url>]
```

### Параметры

| Параметр | Обязательный | По умолчанию | Описание |
|----------|--------------|--------------|----------|
| `-Flavor` | ✅ Да | — | Вариант сборки: standard, iran, china, debug |
| `-ApiUrl` | ❌ Нет | `https://safenetsystem.duckdns.org` | API endpoint |

### Примеры

```powershell
# Стандартная сборка (prod API)
.\build.ps1 -Flavor standard

# Iran build с bundled sing-box
.\build.ps1 -Flavor iran

# China build с VLESS+Reality
.\build.ps1 -Flavor china

# Debug сборка
.\build.ps1 -Flavor debug

# Отладка с прямым IP (НЕ коммитить в master!)
.\build.ps1 -Flavor standard -ApiUrl "http://38.180.253.219:8001"
```

---

## Flavors и ожидаемые размеры

| Flavor   | BUNDLE_HIDDIFY | Размер  | applicationId       | Назначение |
|----------|----------------|---------|---------------------|------------|
| standard | false          | ~5 MB   | com.safenet.vpn     | Основной релиз |
| iran     | true           | ~28 MB  | com.safenet.vpn     | Iran market (sing-box bundled) |
| china    | true           | ~28 MB  | com.safenet.vpn     | China/UAE (VLESS+Reality) |
| debug    | false          | ~5 MB   | com.safenet.vpn     | Отладка |

**Примечание:** Реальный размер может отличаться из-за:
- Включения 3 ABI (arm64-v8a, armeabi-v7a, x86_64)
- `libsingbox.so` = 55.8 MB (для iran/china)
- `libtun2socks.so` = 9.53 MB

**Ожидаемый размер для arm64 только:** ~25-30 MB

---

## API адрес

### Production (по умолчанию)
```
https://safenetsystem.duckdns.org
```

### Отладка (передавать через --dart-define)
```
http://38.180.253.219:8001
```

**ВАЖНО:** Прямой IP **НЕ хардкодится** в `lib/core/constants.dart`.  
Использовать только через `--dart-define=API_BASE_URL=...`

---

## Реестр сборок

После каждой сборки автоматически записывается в:
```
D:\SafeNet\build_registry.csv
```

Формат:
```csv
Date,Flavor,Version,SizeMB,SHA256,ApiUrl
2026-06-27T10:30:00,standard,1.3.2+5,5.2,ABC123...,https://safenetsystem.duckdns.org
```

---

## DEPRECATED скрипты

Следующие скрипты **УСТАРЕЛИ** и будут удалены:
- ❌ `build_standard.ps1` → используйте `.\build.ps1 -Flavor standard`
- ❌ `build_iran.ps1` → используйте `.\build.ps1 -Flavor iran`
- ❌ `build_china.ps1` → используйте `.\build.ps1 -Flavor china`
- ❌ `build_debug.ps1` → используйте `.\build.ps1 -Flavor debug`

---

## ВНИМАНИЕ

### Аномалии размера APK
Если APK > 30 MB для `standard` — это **аномалия**.  
Возможные причины:
1. Split ABI отключён (все 3 ABI включены)
2. Debug-символы не удалены
3. Bundled Hiddify (должен быть только для iran/china)

**Действия:**
1. Проверить: `.\build.ps1 -Flavor standard` (не iran/china)
2. Проверить: `BUNDLE_HIDDIFY=false` в выводе
3. Если размер всё равно >30 MB — остановиться, расследовать, НЕ публиковать

### Проверка перед публикацией
```powershell
# 1. Проверить git status
git status
# Ожидание: working tree clean

# 2. Проверить версию
Select-String -Path pubspec.yaml -Pattern "^version:"

# 3. Собрать standard
.\build.ps1 -Flavor standard

# 4. Проверить размер и SHA256
Get-Item build\app\outputs\flutter-apk\app-standard-release.apk | Select-Object Length, LastWriteTime
Get-FileHash build\app\outputs\flutter-apk\app-standard-release.apk -Algorithm SHA256
```

---

## Правила для агента

1. **Сборка ТОЛЬКО через `build.ps1 -Flavor <name>`.** Запрещено использовать старые `build_*.ps1` напрямую.
2. **Запрещено хардкодить IP/URL в `constants.dart`.** Только `String.fromEnvironment` + `--dart-define`.
3. **Перед сборкой:** `git status` должен быть чист. Незакоммиченные изменения — стоп, эскалация пользователю.
4. **После сборки:** проверить запись в `build_registry.csv` (SHA256 + commit + flavor).
5. **При аномалии размера APK** (>30 MB для standard) — остановиться, расследовать, НЕ публиковать.

---

*Документ создан: 2026-06-27*  
*Автор: qwen/qwen3.7-plus (по заданию Claude Opus 4.8)*
