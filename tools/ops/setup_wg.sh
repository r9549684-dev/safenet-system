#!/bin/bash
set -e

echo "=== [1/6] Checking wireguard-tools ==="
if ! command -v wg &>/dev/null; then
    apt-get update -qq
    apt-get install -y wireguard-tools
fi
wg --version

echo "=== [2/6] Generating WireGuard keypair ==="
mkdir -p /etc/wireguard
chmod 700 /etc/wireguard

wg genkey | tee /etc/wireguard/server_private.key | wg pubkey > /etc/wireguard/server_public.key
chmod 600 /etc/wireguard/server_private.key

SERVER_PRIVATE=$(cat /etc/wireguard/server_private.key)
SERVER_PUBLIC=$(cat /etc/wireguard/server_public.key)
echo "SERVER_PRIVATE: $SERVER_PRIVATE"
echo "SERVER_PUBLIC:  $SERVER_PUBLIC"

echo "=== [3/6] Detecting network interface ==="
IFACE=$(ip route | awk '/^default/ {print $5; exit}')
echo "Default interface: $IFACE"

echo "=== [4/6] Writing /etc/wireguard/wg0.conf ==="
cat > /etc/wireguard/wg0.conf << WGEOF
[Interface]
PrivateKey = $SERVER_PRIVATE
Address = 10.8.0.1/24
ListenPort = 51820
PostUp   = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o $IFACE -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o $IFACE -j MASQUERADE
WGEOF
chmod 600 /etc/wireguard/wg0.conf
echo "wg0.conf written."

echo "=== [5/6] Enabling IP forwarding ==="
sysctl -w net.ipv4.ip_forward=1
grep -q 'net.ipv4.ip_forward=1' /etc/sysctl.conf || echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf

echo "=== [6/6] Starting wg-quick@wg0 ==="
systemctl stop wg-quick@wg0 2>/dev/null || true
systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0
sleep 2
wg show

echo "=== DONE: SERVER_PUBLIC=$SERVER_PUBLIC ==="
