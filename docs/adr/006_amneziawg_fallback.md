# ADR-006: AmneziaWG as Fallback_2 for Russia

**Дата:** 2026-06-26  
**Статус:** Принято  
**Автор:** SafeNet Team + Claude Sonnet 4.6 Reviewer

## Контекст

AmneziaWG — обфусцированный WireGuard для обхода DPI. Использует UDP с обфускацией (Jc, Jmin, Jmax, S1, S2, H1, H2, H3).

## Решение

**AmneziaWG — fallback_2 для России (после VLESS и Trojan).**

### Обоснование:
1. **AmneziaWG обфусцирует WireGuard** — маскирует под случайный UDP трафик
2. **Обфускация**: Jc (junk packets), Jmin/Jmax (размеры), S1/S2 (пакеты), H1/H2/H3 (хэши)
3. **Порт**: 51820 (default WireGuard)
4. **WARNING**: В России AmneziaWG блокируется DPI (data-plane мёртв)

### Почему fallback_2:
- **VLESS+Reality+Fragment** — PRIMARY (обходит TSPU)
- **Trojan+TLS** — fallback_1 (обходит Ростелеком)
- **AmneziaWG** — fallback_2 (блокируется DPI, но может работать в других регионах)

### Обфускация AmneziaWG:
```python
jc = 3          # Junk packets count
jmin = 50       # Min junk packet size
jmax = 1000     # Max junk packet size
s1 = 55         # Obfuscation param 1
s2 = 110        # Obfuscation param 2
h1 = 123456789  # Hash 1
h2 = 987654321  # Hash 2
h3 = 112233445  # Hash 3
```

## Последствия

### Положительные:
- ✅ Полный fallback chain для России: VLESS → Trojan → AmneziaWG → WireGuard
- ✅ Обфускация маскирует WireGuard под случайный UDP
- ✅ Может работать в регионах без строгого DPI

### Отрицательные:
- ⚠️ В России AmneziaWG блокируется DPI (data-plane мёртв)
- ⚠️ UDP блокируется TSPU (Технические средства противодействия угрозам)
- ⚠️ Требуются реальные тесты для подтверждения работоспособности

## Ссылки

- [AmneziaWG Model](../../backend/app/services/xray_models.py#AmneziaWGParams)
- [AmneziaWG Config](../../backend/app/services/xray.py#get_amnezia_config)
- [AmneziaWG Tests](../../test/russia/test_amnezia_wg.py)
