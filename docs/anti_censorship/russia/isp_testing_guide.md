# Russian ISP Testing Guide

**Test SafeNet on all major Russian ISPs. Rostelecom is STRICTEST — if it works there, it works everywhere.**

## ISPs to Test

| ISP | Market Share | DPI | Strictness | Priority |
|-----|--------------|-----|------------|----------|
| Rostelecom | 35% | Sandvine (latest) | STRICTEST | P0 |
| MTS | 25% | Sandvine (older) | Medium | P0 |
| Beeline | 20% | Sandvine (older) | Medium | P0 |
| Megafon | 15% | Sandvine (older) | Medium | P0 |
| Home Networks | 5% | Various | Varies | P1 |

## Test Environment

### Hardware
- **Device**: Redmi Note 9 Pro (test device)
- **SIM**: Russian SIM (Rostelecom, MTS, Beeline, Megafon)
- **Network**: 4G/LTE (mobile data)

### Software
- **Client**: SafeNet Android (latest build)
- **Protocol**: VLESS+Reality+Fragment (primary)
- **SNI**: google.com (primary), cloudflare.com (fallback)
- **Port**: 443 (HTTPS)

## Test Procedure

### Phase 1: Rostelecom (STRICTEST)

#### Step 1: Prepare
```bash
# 1. Insert Rostelecom SIM
# 2. Enable mobile data
# 3. Install SafeNet Android
# 4. Configure VLESS+Reality+Fragment:
#    - SNI: www.google.com
#    - Port: 443
#    - Fragment: tlshello
#    - Fingerprint: chrome
```

#### Step 2: Test Connection
```bash
# 1. Connect via SafeNet
# 2. Check connection success rate
# 3. Measure latency
# 4. Test speed (upload/download)
```

#### Step 3: Test Bypass
```bash
# 1. Access blocked sites (e.g., linkedin.com, medium.com)
# 2. Check if sites load
# 3. Measure time to first byte (TTFB)
```

#### Step 4: Test Durability
```bash
# 1. Keep connection open for 24 hours
# 2. Check if connection stays stable
# 3. Measure detection time (how long before blocked)
```

#### Expected Results (Rostelecom)
- **Connection Success Rate**: >95%
- **Block Resistance**: >80%
- **Detection Time**: >7 days
- **Latency**: <200ms
- **Speed**: >10 Mbps

### Phase 2: MTS/Beeline/Megafon (medium)

#### Repeat Phase 1 for each ISP
```bash
# 1. Insert ISP SIM (MTS, Beeline, Megafon)
# 2. Repeat Step 1-4 from Phase 1
# 3. Compare results with Rostelecom
```

#### Expected Results (MTS/Beeline/Megafon)
- **Connection Success Rate**: >98%
- **Block Resistance**: >90%
- **Detection Time**: >14 days
- **Latency**: <150ms
- **Speed**: >20 Mbps

### Phase 3: Home Networks (varies)

#### Test on different home ISPs
```bash
# 1. Connect to home WiFi (different ISPs)
# 2. Repeat Step 1-4 from Phase 1
# 3. Compare results with mobile ISPs
```

#### Expected Results (Home Networks)
- **Connection Success Rate**: >95%
- **Block Resistance**: >85%
- **Detection Time**: >7 days
- **Latency**: <100ms
- **Speed**: >50 Mbps

## Test Metrics

### Connection Success Rate
```
Definition: Percentage of successful connections
Target: >95% (Rostelecom), >98% (MTS/Beeline/Megafon)
Formula: (successful_connections / total_attempts) * 100
```

### Block Resistance
```
Definition: Percentage of time bypass works
Target: >80%
Formula: (time_bypass_works / total_time) * 100
```

### Detection Time
```
Definition: How long before ISP detects and blocks
Target: >7 days
Measurement: Time from first connection to first block
```

### Latency
```
Definition: Round-trip time (RTT) to server
Target: <200ms (Rostelecom), <150ms (MTS/Beeline/Megafon)
Measurement: ping server_ip
```

### Speed
```
Definition: Upload/download speed
Target: >10 Mbps (Rostelecom), >20 Mbps (MTS/Beeline/Megafon)
Measurement: speedtest.net
```

## Test Results Template

| ISP | Success Rate | Block Resistance | Detection Time | Latency | Speed | Status |
|-----|--------------|------------------|----------------|---------|-------|--------|
| Rostelecom | TBD | TBD | TBD | TBD | TBD | ⏳ PENDING |
| MTS | TBD | TBD | TBD | TBD | TBD | ⏳ PENDING |
| Beeline | TBD | TBD | TBD | TBD | TBD | ⏳ PENDING |
| Megafon | TBD | TBD | TBD | TBD | TBD | ⏳ PENDING |
| Home (ISP1) | TBD | TBD | TBD | TBD | TBD | ⏳ PENDING |

## Troubleshooting

### Connection Fails
```
1. Check SNI (must be google.com for Russia)
2. Check port (must be 443)
3. Check fragment (must be tlshello)
4. Check fingerprint (must be chrome)
5. Test fallback protocol (Trojan+TLS)
```

### Connection Drops
```
1. Check IP rotation (AMO pool)
2. Check server health
3. Check ISP blocking (detection time)
4. Switch to fallback protocol
```

### Slow Speed
```
1. Check server load
2. Check ISP throttling
3. Switch to closer server
4. Test different protocol
```

## References
- [Russian ISP Market](https://en.wikipedia.org/wiki/Internet_in_Russia)
- [Roskomnadzor](https://rkn.gov.ru/) — Russian censorship authority
- [TSPU Patterns](./tspu_patterns.md) — TSPU technical details
- [DPI Sandvine](./dpi_sandvine.md) — DPI vendor analysis
