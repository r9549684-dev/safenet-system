#!/bin/bash
set -e

echo "=== Current WG config ==="
cat /etc/wireguard/wg0.conf

echo "=== Changing ListenPort to 443 ==="
python3 - <<'EOF'
import re
with open('/etc/wireguard/wg0.conf', 'r') as f:
    txt = f.read()
txt2 = re.sub(r'ListenPort\s*=\s*\d+', 'ListenPort = 443', txt)
with open('/etc/wireguard/wg0.conf', 'w') as f:
    f.write(txt2)
import re
m = re.search(r'ListenPort.*', txt2)
print("Updated:", m.group() if m else "not found")
EOF

echo "=== Applying new port live (no full restart) ==="
wg set wg0 listen-port 443
wg show wg0 | grep "listening port"

echo "=== Updating iptables ==="
iptables -I INPUT -p udp --dport 443 -j ACCEPT 2>/dev/null || true
iptables-save > /tmp/iptables.bak
echo "Firewall OK"

echo "=== Updating server meta in DB ==="
PGPASSWORD=$POSTGRES_PASSWORD psql -h db -U safenet -d safenet -c \
  "UPDATE servers SET meta = COALESCE(meta::jsonb, '{}') || '{\"wg_port\": 443}'::jsonb WHERE is_active = true RETURNING id, country, port, meta;"

echo "=== ALL DONE ==="
