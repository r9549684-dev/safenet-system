# ADR-005: Russia as PRIMARY Target for Anti-Censorship

**Дата:** 2026-06-26  
**Статус:** Принято  
**Автор:** SafeNet Team + GPT-5.5 Reviewer

## Контекст

SafeNet — система обхода цензуры через secure tunnel. Россия имеет одну из самых продвинутых систем цензуры в мире (TSPU, DPI Sandvine). Если SafeNet обходит российскую цензуру, он автоматически может обходить блокировки в других странах.

## Решение

**Россия — PRIMARY target для anti-censorship.**

### Обоснование:
1. **TSPU (Technical Service for Counteracting Threats)** — одна из самых продвинутых систем DPI в мире
2. **DPI Sandvine** — используется Ростелекомом (строгий DPI)
3. **Блокировки**: SNI blocking, TLS fragmentation, UDP blocking, IP blocking
4. **Если SafeNet обходит TSPU + Sandvine → обходит все остальные**

### Fallback Order для России:
```
1. VLESS+Reality+Fragment (PRIMARY) — обходит TSPU
2. Trojan+TLS (fallback_1) — обходит Ростелеком
3. AmneziaWG (fallback_2) — блокируется DPI (data-plane мёртв)
4. WireGuard (не работает в России)
```

### SNI для России:
- **Primary**: www.google.com (trusted by TSPU)
- **Fallback**: www.cloudflare.com (trusted CDN)

### Протоколы:
- **VLESS+Reality+Fragment**: SNI = google.com, Fragment = tlshello, Port = 443
- **Trojan+TLS**: SNI = google.com, Port = 443, insecure = True (self-signed)
- **AmneziaWG**: Port = 51820, UDP, obfuscation (Jc, Jmin, Jmax, S1, S2, H1, H2, H3)

## Последствия

### Положительные:
- ✅ Если SafeNet обходит Россию → обходит все остальные страны
- ✅ Чёткий fallback order для России
- ✅ Документация TSPU patterns, DPI Sandvine analysis
- ✅ Тесты для российских провайдеров (Rostelecom, MTS, Beeline, Megafon)

### Отрицательные:
- ⚠️ AmneziaWG блокируется DPI в России (data-plane мёртв)
- ⚠️ Trojan insecure=True (MITM risk) — требуется certificate pinning
- ⚠️ Требуются реальные тесты на Ростелекоме (пока только unit-тесты)

## Ссылки

- [TSPU Patterns](../anti_censorship/russia/tspu_patterns.md)
- [DPI Sandvine Analysis](../anti_censorship/russia/dpi_sandvine.md)
- [ISP Testing Guide](../anti_censorship/russia/isp_testing_guide.md)
- [Regional Profiles](../../backend/app/services/regional_profiles.py)
