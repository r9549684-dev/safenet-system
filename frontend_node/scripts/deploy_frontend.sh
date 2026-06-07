#!/bin/bash
# Скрипт автоматического развертывания Входного Шлюза (Frontend-ноды) SafeNet VPN
# Принцип: Транзит без следов. Никаких логов на диске, только RAM.

set -e
export DEBIAN_FRONTEND=noninteractive

echo "[+] Базовая подготовка и удаление систем логирования..."
apt-get update -qq
apt-get remove -y --purge rsyslog systemd-journal-* || true
apt-get autoremove -y -qq

echo "[+] Настройка файловой системы без следов (noatime, tmpfs для логов)..."
# Монтируем /var/log в оперативную память (tmpfs), чтобы при перезагрузке или изъятии диска следов не осталось
echo "tmpfs /var/log tmpfs defaults,noatime,mode=0755,size=50M 0 0" >> /etc/fstab
mount -a

# Очистка истории и временных файлов
rm -rf /var/log/*
rm -rf /tmp/*
history -c
history -w

echo "[+] Установка транзитных компонентов (WireGuard / Amnezia / Byedpi)..."
# Здесь устанавливаются только необходимые транзитные пакеты без логирования
apt-get install -y -qq wireguard knockd curl jq

echo "[+] Настройка сети для чистого NAT без сохранения состояний дольше необходимого..."
# Включаем форвардинг
echo 1 > /proc/sys/net/ipv4/ip_forward

# Базовые правила iptables для транзита (без логирования dropped пакетов)
iptables -F
iptables -t nat -F
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Разрешаем WireGuard порт (например, 51820) и установленные соединения
iptables -A INPUT -p udp --dport 51820 -j ACCEPT
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

echo "[+] Очистка bash-истории и завершение..."
rm -f ~/.bash_history
unset HISTFILE
echo "[+] Frontend-нода развернута в режиме 'Zero Footprint'. Готов к транзиту."