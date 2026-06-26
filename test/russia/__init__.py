"""Tests for Russia anti-censorship (PRIMARY target).

If SafeNet bypasses Russian censorship (TSPU, DPI Sandvine),
it bypasses all others automatically.

Russian ISPs to test:
1. Rostelecom — STRICTEST (blocks UDP, strict DPI)
2. MTS — medium DPI (blocks some VPNs)
3. Beeline — medium DPI (selective blocking)
4. Megafon — medium DPI (selective blocking)
5. Home networks — various DPI (test each)

Metrics:
- Block Resistance >80%
- Detection Time >7 days
- Connection Success Rate >95% via Rostelecom
"""
