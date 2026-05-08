import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

def debug_keys():
    keys = [os.getenv(f"RAPID_API_KEY{i}") for i in range(1, 14) if os.getenv(f"RAPID_API_KEY{i}")]
    results = {}
    
    host = "google-map-places.p.rapidapi.com"
    
    for i, key in enumerate(keys):
        headers = {"x-rapidapi-key": key, "x-rapidapi-host": host}
        try:
            resp = httpx.get(
                f"https://{host}/maps/api/place/findplacefromtext/json",
                headers=headers,
                params={"input": "Hanoi", "inputtype": "textquery"},
                timeout=5
            )
            results[f"KEY_{i+1}"] = {
                "status": resp.status_code,
                "body": resp.json() if resp.status_code != 200 else "OK"
            }
            print(f"Key {i+1}: {resp.status_code}")
            if resp.status_code != 200:
                print(f"   Message: {resp.text}")
        except Exception as e:
            results[f"KEY_{i+1}"] = str(e)
            
    with open("storage/logs/key_debug_full.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    debug_keys()
