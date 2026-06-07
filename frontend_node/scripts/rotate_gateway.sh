#!/bin/bash
# Скрипт мгновенной ротации Входного Шлюза (Frontend-ноды)
# Уничтожает скомпрометированный шлюз и поднимает новый, уведомляя Центр.

set -e

GATEWAY_ID=$1
MASTER_IP=$2
API_TOKEN=$3

if [ -z "$GATEWAY_ID" ] || [ -z "$MASTER_IP" ]; then
    echo "Использование: $0 <gateway_id> <master_ip> [api_token]"
    exit 1
fi

echo "[+] Этап 1: Уничтожение скомпрометированного шлюза $GATEWAY_ID..."
# Имитация вызова API облачного провайдера для уничтожения инстанса
# curl -s -X DELETE "https://api.cloudprovider.com/v1/instances/$GATEWAY_ID" -H "Authorization: Bearer $API_TOKEN"
echo "destroy instance $GATEWAY_ID" 

echo "[+] Этап 2: Создание нового чистого шлюза..."
# Имитация создания нового инстанса
# NEW_INSTANCE_ID=$(curl -s -X POST "https://api.cloudprovider.com/v1/instances" ...)
NEW_INSTANCE_ID="gw-$(date +%s)"
echo "create instance $NEW_INSTANCE_ID"

echo "[+] Этап 3: Ожидание готовности (timeout 180s)..."
# Ожидание инициализации облачного сервера (до 3 минут)
timeout 180 bash -c 'until nc -z $MASTER_IP 22; do sleep 5; done' || echo "Warning: SSH not immediately available, proceeding with API sync"

echo "[+] Этап 4: Получение нового IP и синхронизация с Центром..."
# Получаем публичный IP нового шлюза (или берем из API провайдера)
NEW_IP=$(curl -s https://api.ipify.org)

echo "[+] Этап 5: Port Knocking для открытия доверенного канала к Центру..."
knock "$MASTER_IP" 7000 8000 9000

# Небольшая пауза, пока knockd на мастере обрабатывает запрос и открывает порт
sleep 3

echo "[+] Этап 6: Регистрация нового шлюза в базе данных Центра..."
# Отправляем новый IP на Управляющий узел по защищенному (теперь открытому) каналу
curl -s -X POST "http://$MASTER_IP/api/v1/gateways/register" -H "Content-Type: application/json" -d "{\"gateway_id\": \"$NEW_INSTANCE_ID\", \"ip\": \"$NEW_IP\", \"status\": \"active\"}"

echo "[+] Ротация успешно завершена. Новый шлюз $NEW_INSTANCE_ID ($NEW_IP) активен и синхронизирован."