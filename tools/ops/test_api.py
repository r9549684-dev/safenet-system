import urllib.request
import urllib.error
import json
import sys

BASE = "http://localhost:8500"

SEP = "=" * 60

# === Шаг 1: POST /auth/device ===
print("=" * 60)
print("STEP 1: POST /auth/device")
print("=" * 60)

payload = json.dumps({"device_id": "test-device-warp-001"}).encode()
req = urllib.request.Request(
    BASE + "/auth/device",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        body = r.read().decode()
        print("Status:", r.status)
        print("Response:", body)
        data = json.loads(body)
        token = data.get("access_token", "")
        print("access_token:", token[:50] + "..." if len(token) > 50 else token)
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print("HTTP Error:", e.code, body)
    sys.exit(1)
except Exception as e:
    print("Error:", e)
    sys.exit(1)

print()

# === Шаг 2: GET /servers — найти ID первого сервера ===
print("=" * 60)
print("STEP 2: GET /servers")
print("=" * 60)

req2 = urllib.request.Request(
    BASE + "/servers",
    headers={"Authorization": "Bearer " + token},
    method="GET"
)
server_id = None
try:
    with urllib.request.urlopen(req2, timeout=10) as r:
        body2 = r.read().decode()
        print("Status:", r.status)
        print("Response:", body2[:500])
        servers = json.loads(body2)
        srv_list = None
        if isinstance(servers, list):
            srv_list = servers
        elif isinstance(servers, dict):
            for k in ["servers", "items", "data", "results"]:
                if k in servers and isinstance(servers[k], list):
                    srv_list = servers[k]
                    break
        if srv_list and len(srv_list) > 0:
            server_id = str(srv_list[0].get("id", ""))
            print("First server id:", server_id)
        else:
            print("No servers found, trying id=1 as fallback")
            server_id = "1"
except urllib.error.HTTPError as e:
    body2 = e.read().decode()
    print("HTTP Error:", e.code, body2)
    print("Trying numeric server_id=1 as fallback")
    server_id = "1"
except Exception as e:
    print("Error:", e)
    server_id = "1"

print()

# === Шаг 3: POST /vpn/connect/{server_id} ===
print("=" * 60)
print("STEP 3: POST /vpn/connect/" + str(server_id))
print("=" * 60)

req3 = urllib.request.Request(
    BASE + "/vpn/connect/" + str(server_id),
    data=b"{}",
    headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
    },
    method="POST"
)
try:
    with urllib.request.urlopen(req3, timeout=10) as r:
        body3 = r.read().decode()
        print("Status:", r.status)
        print("Response:", body3)
        d = json.loads(body3)
        print()
        print("--- KEY FIELDS ---")
        for k in ["wg_config", "assigned_ip", "byedpi_profile", "protocol", "server_id"]:
            v = d.get(k, "MISSING")
            if k == "wg_config" and v != "MISSING":
                lines = v.split("\n")
                print(f"{k}: [{len(lines)} lines, starts with: {lines[0]}]")
            else:
                print(f"{k}: {v}")
except urllib.error.HTTPError as e:
    err_body = e.read().decode()
    print("HTTP Error:", e.code)
    print("Error body:", err_body)
except Exception as e:
    print("Error:", e)

print()
print("=" * 60)
print("DONE")
print("=" * 60)
