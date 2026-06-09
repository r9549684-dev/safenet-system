# SafeNet service

service-сервис для обхода цензуры. Flutter (Android) + FastAPI backend. Поддержка WireGuard, AmneziaWG, VLESS+Reality+Fragment (sing-box), ByeDPI.

## Рынки
- **ОАЭ** — основной активный рынок (Etisalat/Du DPI, высокая платёжеспособность)
- **Иран** — на паузе (блокаут ~1% с 28.02.2026, возобновление после Новруза ~20.03.2026)
- **Турция** — в плане

## Быстрый старт

```bash
# Backend (Docker)
cd infra && docker compose up -d

# Flutter
flutter pub get
flutter run

# Сборка APK
.\build_standard.ps1   # обычный
.\build_iran.ps1       # Иран (bundleSingbox=true, страна=IR)
.\build_china.ps1      # Китай/ОАЭ (bundleSingbox=true, страна=AE)
```

## API
- **Prod:** https://api.loveaibot.net
- **Direct:** http://89.208.107.67:8500
- **Docs:** [DOCUMENTATION.md](./DOCUMENTATION.md)
