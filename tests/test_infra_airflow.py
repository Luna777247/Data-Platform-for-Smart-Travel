import unittest
import requests
import os
from requests.auth import HTTPBasicAuth

class TestAirflowAPI(unittest.TestCase):
    def test_connectivity(self):
        url = "http://localhost:8080/api/v1/dags"
        user = os.getenv("AIRFLOW_USER", "admin")
        pw = os.getenv("AIRFLOW_PASSWORD", "admin")
        
        try:
            response = requests.get(url, auth=HTTPBasicAuth(user, pw), timeout=5)
            if response.status_code == 200:
                print("✅ Airflow API is reachable.")
            else:
                print(f"⚠️ Airflow returned {response.status_code}")
        except Exception as e:
            print(f"❌ Airflow unreachable: {e}")

if __name__ == "__main__":
    unittest.main()
