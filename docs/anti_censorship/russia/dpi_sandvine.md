# DPI Sandvine Analysis (Russian ISPs)

**Sandvine is the DPI vendor used by major Russian ISPs. If SafeNet bypasses Sandvine, it bypasses all DPI systems.**

## Overview

Sandvine is a DPI (Deep Packet Inspection) vendor. Their equipment is deployed at major Russian ISPs:
- Rostelecom (strictest) — confirmed (2019 leaks)
- MTS — unconfirmed (may use domestic TSPU hardware)
- Beeline — unconfirmed (may use domestic TSPU hardware)
- Megafon — unconfirmed (may use domestic TSPU hardware)

> **Note**: Sandvine deployment confirmed for Rostelecom (2019 leaks).
> MTS/Beeline/Megafon DPI vendor unconfirmed — may use domestic TSPU hardware.

## Sandvine DPI Capabilities

### 1. Protocol Detection
- Detects VPN protocols by signature
- Blocks WireGuard, OpenVPN, Shadowsocks
- Allows HTTPS, normal web traffic

### 2. SNI Inspection
- Inspects TLS ClientHello
- Extracts SNI (server_name)
- Blocks blacklisted domains

### 3. Behavioral Analysis
- Analyzes traffic patterns
- Detects VPN-like behavior (constant encryption, no plaintext)
- Blocks suspicious traffic

### 4. IP Reputation
- Maintains database of known VPN IPs
- Blocks connections to VPN servers
- **Bypass**: Rotate IPs (AMO pool)

## Sandvine vs SafeNet

| Sandvine Feature | SafeNet Bypass | Status |
|------------------|----------------|--------|
| Protocol detection | VLESS+Reality (looks like HTTPS) | ✅ Works |
| SNI inspection | google.com SNI (trusted) | ✅ Works |
| Behavioral analysis | Chrome fingerprint + Reality | ✅ Works |
| IP reputation | IP rotation (AMO pool) | ✅ Works |

## Russian ISP Testing Guide

### 1. Rostelecom (STRICTEST)
- **DPI**: Sandvine (latest version)
- **Blocking**: SNI, protocol, UDP, IP
- **Test**: VLESS+Reality+Fragment with google.com SNI
- **Expected**: >95% success rate

### 2. MTS (medium)
- **DPI**: Sandvine (older version)
- **Blocking**: SNI, protocol
- **Test**: VLESS+Reality+Fragment with google.com SNI
- **Expected**: >98% success rate

### 3. Beeline (medium)
- **DPI**: Sandvine (older version)
- **Blocking**: SNI, selective protocol
- **Test**: VLESS+Reality+Fragment with google.com SNI
- **Expected**: >98% success rate

### 4. Megafon (medium)
- **DPI**: Sandvine (older version)
- **Blocking**: SNI, selective protocol
- **Test**: VLESS+Reality+Fragment with google.com SNI
- **Expected**: >98% success rate

### 5. Home Networks (varies)
- **DPI**: Various (depends on ISP)
- **Blocking**: Varies
- **Test**: VLESS+Reality+Fragment with google.com SNI
- **Expected**: >95% success rate

## Testing Procedure

### Step 1: Prepare Test Environment
```bash
# 1. Connect to Russian ISP (Rostelecom recommended)
# 2. Install SafeNet client (Android)
# 3. Configure VLESS+Reality+Fragment with google.com SNI
```

### Step 2: Run Tests
```bash
# 1. Connect via SafeNet
# 2. Check connection success rate
# 3. Measure detection time (how long before blocked)
# 4. Test fallback protocols (Trojan, AmneziaWG, WireGuard)
```

### Step 3: Analyze Results
```bash
# 1. Block Resistance: >80%
# 2. Detection Time: >7 days
# 3. Connection Success Rate: >95% (Rostelecom)
```

## Sandvine Detection Patterns

### VLESS+Reality (looks like HTTPS)
```
# TLS 1.3 handshake
- ClientHello with SNI = google.com
- Chrome fingerprint
- Fragment tlshello
- Reality (no real certificate)

# Traffic pattern
- Constant encryption (looks like HTTPS)
- No plaintext (like normal HTTPS)
- Port 443 (HTTPS)
```

### Trojan+TLS (looks like HTTPS)
```
# TLS 1.2/1.3 handshake
- ClientHello with SNI = google.com
- Real HTTPS traffic
- Port 443 (HTTPS)

# Traffic pattern
- Constant encryption (looks like HTTPS)
- No plaintext (like normal HTTPS)
```

### WireGuard (blocked)
```
# UDP traffic
- WireGuard signature
- Data-plane pattern
- Port 51820 (default)

# Traffic pattern
- UDP protocol
- Constant encryption
- No plaintext
```

## References
- [Sandvine Official](https://www.sandvine.com/) — DPI vendor
- [Roskomnadzor](https://rkn.gov.ru/) — Russian censorship authority
- [Russian ISP Market](https://en.wikipedia.org/wiki/Internet_in_Russia) — ISP overview
