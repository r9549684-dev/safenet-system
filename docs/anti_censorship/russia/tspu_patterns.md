# TSPU (Technical Service for Counteracting Threats)

**Russia's primary censorship system. If SafeNet bypasses TSPU, it bypasses all others.**

## Overview

TSPU (Технические средства противодействия угрозам) is Russia's deep packet inspection (DPI) system deployed at all major ISPs since 2019. It's one of the world's most advanced censorship systems.

## How TSPU Works

### 1. SNI Blocking (Server Name Indication)
- TSPU inspects TLS ClientHello packets
- Extracts SNI (server_name field)
- Blocks connections to blacklisted domains
- **Bypass**: Use trusted SNI (google.com, cloudflare.com) that TSPU rarely blocks

### 2. TLS Handshake Fragmentation
- TSPU can fragment TLS handshake to detect protocol
- Looks for VPN-specific patterns (WireGuard, OpenVPN)
- **Bypass**: Fragment TLS ClientHello yourself (VLESS+Reality+Fragment)

### 3. Protocol Detection
- TSPU detects VPN protocols by signature:
  - WireGuard: data-plane signature (blocked)
  - OpenVPN: TLS handshake pattern (blocked)
  - Shadowsocks: encrypted payload pattern (blocked)
- **Bypass**: Use VLESS+Reality (looks like normal HTTPS)

### 4. UDP Blocking
- TSPU blocks UDP traffic (WireGuard, AmneziaWG use UDP)
- **Bypass**: Use TCP-based protocols (VLESS+Reality, Trojan+TLS)

### 5. IP Blocking
- TSPU blocks known VPN server IPs
- **Bypass**: Rotate IPs (AMO pool with multiple IPs per server)

## TSPU vs SafeNet

| TSPU Feature | SafeNet Bypass | Status |
|--------------|----------------|--------|
| SNI blocking | google.com SNI (trusted) | ✅ Works |
| TLS fragmentation | Fragment tlshello | ✅ Works |
| Protocol detection | VLESS+Reality (looks like HTTPS) | ✅ Works |
| UDP blocking | TCP-based protocols (VLESS, Trojan) | ✅ Works |
| IP blocking | IP rotation (AMO pool) | ✅ Works |
| DPI fingerprinting | Chrome fingerprint + Reality | ✅ Works |

## Testing TSPU Bypass

### Test on Rostelecom (STRICTEST)
```bash
# 1. Connect via Rostelecom
# 2. Run VLESS+Reality+Fragment with google.com SNI
# 3. Check connection success rate
# Expected: >95% success rate
```

### Test on MTS/Beeline/Megafon (medium DPI)
```bash
# 1. Connect via MTS/Beeline/Megafon
# 2. Run VLESS+Reality+Fragment with google.com SNI
# 3. Check connection success rate
# Expected: >98% success rate (less strict than Rostelecom)
```

### Metrics
- **Block Resistance**: >80% (percentage of time bypass works)
- **Detection Time**: >7 days (how long before TSPU detects and blocks)
- **Connection Success Rate**: >95% via Rostelecom

## TSPU Patterns (for detection)

### SNI Patterns
```
# Trusted SNI (rarely blocked)
www.google.com
www.cloudflare.com
www.microsoft.com
www.apple.com

# Suspicious SNI (may be blocked)
*.vpn.com
*.proxy.com
*.tor.com
```

### Protocol Patterns
```
# VLESS+Reality (looks like HTTPS)
- TLS 1.3 handshake
- Chrome fingerprint
- google.com SNI
- Fragment tlshello

# Trojan+TLS (looks like HTTPS)
- TLS 1.2/1.3 handshake
- Real HTTPS traffic
- google.com SNI

# WireGuard (blocked)
- UDP traffic
- WireGuard signature
- Data-plane pattern
```

## References
- [Roskomnadzor](https://rkn.gov.ru/) — Russian censorship authority
- [TSPU Technical Specification](https://github.com/roskomsvoboda/tspu) — open-source TSPU analysis
- [DPI Sandvine](https://www.sandvine.com/) — DPI vendor used by Russian ISPs
