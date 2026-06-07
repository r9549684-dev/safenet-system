#!/bin/bash
# Скрипт автоматического развертывания Рабочего Узла (Backend-ноды) SafeNet VPN
# Принцип: Абсолютная изоляция. Принимает трафик ТОЛЬКО от доверенных Входных шлюзов.

set -e
export DEBIAN_FRONTEND=noninteractive

# Переменные окружения (задаются облачным провайдером или мастер-скриптом)
FRONTEND_IP=${1:-"10.0.0.0/8"} # По умолчанию разрешаем только приватную сеть или конкретный IP шлюза
WG_PORT=${2:-51821}

echo "[+] Этап 1: Полное отключение логирования и очистка следов..."
apt-get remove -y --purge rsyslog systemd-journal-* || true
apt-get autoremove -y -qq
echo "tmpfs /var/log tmpfs defaults,noatime,mode=0755,size=50M 0 0" >> /etc/fstab
mount -a
rm -rf /var/log/*
history -c

echo "[+] Этап 2: Установка WireGuard для скрытого туннелирования..."
apt-get update -qq
apt-get install -y -qq wireguard-tools jq curl

echo "[+] Этап 3: Жесткая сетевая изоляция (Backend принимает трафик ТОЛЬКО от Frontend)..."
iptables -F
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Разрешаем loopback
iptables -A INPUT -i lo -j ACCEPT

# РАЗРЕШАЕМ ВХОДЯЩИЙ ТРАФИК ТОЛЬКО С ДОВЕРЕННЫХ IP ВХОДНЫХ ШЛЮЗОВ
iptables -A INPUT -s "$FRONTEND_IP" -p udp --dport "$WG_PORT" -j ACCEPT

# Разрешаем установленные соединения (для ответа внутри туннеля)
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# NAT для выхода в интернет через основной интерфейс (eth0)
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Сохраняем правила
netfilter-persistent save

echo "[+] Этап 4: Генерация ключей WireGuard и базовая настройка туннеля..."
wg genkey | tee /etc/wireguard/privatekey | wg pubkey > /etc/wireguard/publickey
chmod 600 /etc/wireguard/privatekey

cat <<EOF > /etc/wireguard/wg0.conf
[Interface]
PrivateKey = $(cat /etc/wireguard/privatekey)
Address = 10.200.0.2/24
ListenPort = $WG_PORT

# Строгая изоляция: трафик разрешен только для подсети туннеля
# AllowedIPs = 10.200.0.0/24
EOF

echo "[+] Этап 5: Запуск и включение автозагрузки туннеля..."
wg-quick up wg0
systemctl enable wg-quick@wg0

echo "[+] Backend-нода развернута. Изоляция активна. Ожидание подключения от Frontend IP: $FRONTEND_IP"