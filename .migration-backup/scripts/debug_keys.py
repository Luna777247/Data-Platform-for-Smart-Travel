import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.shared.path_manager import KEY_REPORT_PATH, DOTENV_PATH
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv(DOTENV_PATH)
host = "google-map-places.p.rapidapi.com"
results = {}

for i in range(1, 14):
    key_name = f"RAPID_API_KEY{i}"
    key = os.getenv(key_name)
    if not key: continue
    
    try:
        resp = httpx.get(
            f"https://{host}/maps/api/place/findplacefromtext/json",
            headers={"x-rapidapi-key": key, "x-rapidapi-host": host},
            params={"input": "Hanoi", "inputtype": "textquery"},
            timeout=10
        )
        results[key_name] = resp.status_code
    except Exception as e:
        results[key_name] = f"ERROR: {str(e)[:20]}"

with open(KEY_REPORT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"✅ Key report saved to {KEY_REPORT_PATH}")
