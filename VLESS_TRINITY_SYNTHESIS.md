# VLESS Trinity Synthesis Report

**Date:** 2026-06-23
**Participants:** Alpha (owl-alpha), Beta (qwen3.7-plus), Judge (claude-sonnet-4.6), Gamma (kimi-k2.7-code)
**All calls via OpenRouter API, real models.**

---

## Executive Summary

**Корневая проблема — 3 слоя, а не 2:**

1. **Flutter layer** — НЕ читает `vless_config` из AMO pool (root cause)
2. **Converter layer** — где расположить raw dict → singbox JSON (Python vs Kotlin)
3. **Android layer** — уже есть `buildSingboxConfig()`, нужна VLESS outbound ветка

Ни Alpha, ни Beta не решили слой #1. Judge назвал это первым blind spot.

---

## Trinity Verdicts

### Judge (claude-sonnet-4.6) — Quality Assessment

| Role | Rigor | Evidence | Honesty | Overall |
|------|-------|----------|---------|---------|
| Alpha | 5/10 | 4/10 | 5/10 | **5/10** |
| Beta | 5/10 | 4/10 | 5/10 | **5/10** |

**Verdict:** FAIL — оба отчёта слабы для принятия решения. Нужен передел с учётом Flutter-слоя.

**Key blind spots (Judge):**
- Alpha missed: механизм передачи в AMO pool, Pydantic схему VLESS, backward compatibility
- Beta missed: iOS parity, MethodChannel контракт, VPN session lifecycle
- **Both missed:** корневая проблема — Flutter не читает vless_config из AMO pool

### Gamma (kimi-k2.7-code) — Cross-reference & Blind Spots

**10 blind spots detected (8 HIGH severity):**

| # | Category | Severity | Issue |
|---|----------|----------|-------|
| 1 | technical | HIGH | Нет версионирования sing-box schema |
| 2 | technical | HIGH | Нет валидации входного raw dict и выходного singbox JSON |
| 3 | deployment | HIGH | Нет стратегии gradual rollout (big-bang risk) |
| 4 | monitoring | HIGH | Нет observability: метрики, алерты, handshake latency |
| 5 | deployment | HIGH | Нет rollback плана/kill-switch |
| 6 | technical | HIGH | Reality key management и ротация |
| 7 | testing | MEDIUM | Нет E2E тестовой стратегии |
| 8 | technical | MEDIUM | Фрагментация sing-box версий на клиентах |
| 9 | deployment | MEDIUM | Нет документации (API, integration guide) |
| 10 | technical | MEDIUM | Trust boundary для Reality ключей |

**Contradictions (Alpha vs Beta):**
- Centralized control (Alpha) vs offline autonomy (Beta) → Resolution: **hybrid** — backend validates+signs, client caches
- Schema updates: server-side (Alpha) vs client-side (Beta) → Resolution: critical logic на backend, adapter layer на клиенте

---

## Trinity Consensus: Recommended Approach

### Phase 0 (BLOCKING) — Flutter AMO Pool Reader

**Без этого ни один конвертер не работает.**

- `pool_response.dart` — добавить `vlessConfig` field в VpnConfigItem
- `vpn_service.dart` — читать `vless_config` из AMO pool item
- Убрать/ослабить `bundleSingbox=false` gate для VLESS path

**Estimate:** 4-6h

### Phase 1 — Python Backend Converter (Alpha's choice, Gamma-enhanced)

Почему Python > Kotlin:
- Security: Reality keys не уходят на клиент в сыром виде
- Единая точка валидации (JsonSchema/Pydantic на входе И выходе)
- Backend already имеет raw dict — нулевой overhead передачи
- Schema versioning (`singbox_schema_version` field) — легко менять без обновления APK
- Тестируется unit-тестами без эмуляторов

**Что добавить (из Gamma):**
- Pydantic модель `VlessRealityParams` (uuid, flow, serverName, shortId, publicKey, spiderX)
- `build_singbox_config()` → `dict` с full singbox schema
- JSON Schema validator на входе и выходе
- `singbox_schema_version` в raw dict
- Feature flag `vless_reality_enabled` per user/region

**Estimate:** 6-8h

### Phase 2 — Kotlin Android Adapter

- `SingboxVpnService` получает ПОЛНЫЙ singbox JSON из Flutter (не raw dict)
- Минимальная логика: validation + start/stop lifecycle
- TUN fd lifecycle management (stop BEFORE WG start)
- Handle `transport.type != tcp` for vision flow (sing-box 1.12+ FATAL)

**Estimate:** 4-6h

### Phase 3 — Failover + Deployment + Monitoring

- VLESS→AWG failover (< 30s)
- Feature flag rollout (canary → 100%)
- Metrics: `converter.success`, `converter.validation_failed`, `singbox.connect_time`, `singbox.handshake_error`
- Rollback kill-switch: `force_legacy_protocol` remote config
- Telemetry: `protocol_type` distribution, failover rate

**Estimate:** 4-6h

**Total:** 18-26h

---

## Critical Blockers (Must Solve Before Implementation)

1. **Flutter AMO reader** — без этого VLESS config не достигает Android layer
2. **sing-box 1.12+ FATAL** — `transport.type=tcp` для vision flow НЕ поддерживается, нужен другой transport
3. **Reality key security** — privateKey НЕ должен попадать на клиент
4. **Schema versioning** — prevent silent breakage при обновлении sing-box ядра

---

## Anti-patterns (DO NOT)

- Hardcode sing-box JSON шаблоны в Flutter
- Хранить Reality privateKey на клиенте
- Big-bang migration без feature flag
- Игнорировать iOS parity (даже если сейчас Android-only, архитектура должна допускать)
- Делать Kotlin-конвертер с полным raw dict → singbox JSON (дублирование, drift risk)

---

## Data

- Alpha report: `C:\Users\53\_trinity_judge.py` (contains alpha_report)
- Beta report: `C:\Users\53\_trinity_beta.py` (if created)
- Judge verdict: `C:\Users\53\_trinity_judge.py` (output above)
- Gamma cross-reference: `C:\Users\53\_trinity_gamma.py` (output above)
