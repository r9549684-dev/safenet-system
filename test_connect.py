import urllib.request, json, sys

BASE = "http://89.208.107.67:8500"

# 1. Get token
req = urllib.request.Request(
    BASE + "/auth/device",
    data=json.dumps({"device_id": "test-device-warp-001"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
resp = urllib.request.urlopen(req)
token = json.loads(resp.read())["access_token"]
print("TOKEN OK:", token[:40], "...")

# 2. Test /service/connect/3
req2 = urllib.request.Request(
    BASE + "/service/connect/3",
    data=b"{}",
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    method="POST"
)
try:
    resp2 = urllib.request.urlopen(req2)
    data = json.loads(resp2.read())
    print("STATUS: 200 OK")
    print("wg_config:", data.get("wg_config", "")[:60], "...")
    print("mode:", data.get("mode"))
except urllib.error.HTTPError as e:
    print(f"STATUS: {e.code} {e.reason}")
    print(e.read().decode())
