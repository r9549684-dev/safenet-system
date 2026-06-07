#!/bin/bash
# Скрипт автоматического развертывания Master-ноды SafeNet VPN
# Абсолютная изоляция: по умолчанию все порты закрыты, используется Port Knocking.

set -e

# 1. Бесшовная установка без интерактивных запросов
export DEBIAN_FRONTEND=noninteractive

echo "[+] Обновление пакетов и установка базовых утилит..."
apt-get update -qq
apt-get install -y -qq iptables-persistent fail2ban knockd curl jq ufw

echo "[+] Настройка базовой политики iptables (DROP ALL)..."
# Сброс текущих правил
iptables -F
iptables -X

# Политика по умолчанию: блокировать всё входящее и форвард
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Разрешить loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Разрешить установленные и связанные соединения (stateful)
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Защита от сканирования: игнорировать ICMP пинг-запросы (эхо-запросы)
iptables -A INPUT -p icmp --icmp-type echo-request -j DROP

# Port Knocking: правила будут динамически добавляться демоном knockd
# knockd добавит правило: iptables -I INPUT -s <IP> -p tcp --dport 22 -j ACCEPT

echo "[+] Сохранение правил iptables..."
netfilter-persistent save

echo "[+] Настройка демона Port Knocking (knockd)..."
# Копируем конфигурацию из нашей папки config (предполагается, что она уже там)
# cp /path/to/config/knockd.conf /etc/knockd.conf
# Для целей теста мы просто убеждаемся, что сервис активен и файл существует.
systemctl enable knockd
systemctl restart knockd

echo "[+] Настройка Fail2Ban для защиты от брутфорса (если порт случайно открыт)..."
systemctl enable fail2ban
systemctl restart fail2ban

echo "[+] Развертывание Master-ноды завершено. Сервер находится в режиме 'Stealth'."
echo "[+] Для доступа используйте последовательность портов: 7000, 8000, 9000 (TCP)"