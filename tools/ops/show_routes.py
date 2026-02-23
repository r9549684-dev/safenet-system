import json
d = json.load(open("/tmp/oa.json"))
print("=== ROUTES ===")
for path, methods in d["paths"].items():
    for method in methods:
        print(f"  {method.upper():6} {path}")
