"""
Test All API Endpoints
======================

Test các API endpoints chính và ghi nhận kết quả.
"""

import requests
import json


BASE_URL = "http://localhost:8000"


def get_token():
    """Get JWT token."""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    return response.json().get("access_token")


def test_endpoint(method, path, params=None, data=None, description=""):
    """Test một endpoint."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    url = f"{BASE_URL}{path}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            return {"status": "error", "message": "Unsupported method"}
        
        if response.status_code == 200:
            result = response.json()
            return {
                "status": "✅",
                "status_code": response.status_code,
                "description": description,
                "result": result
            }
        else:
            return {
                "status": "❌",
                "status_code": response.status_code,
                "description": description,
                "error": response.text[:100]
            }
    except Exception as e:
        return {
            "status": "❌",
            "description": description,
            "error": str(e)[:100]
        }


def run_api_tests():
    """Run all API tests."""
    print("🚀 Testing API Endpoints...")
    print("=" * 60)
    
    tests = [
        # Auth endpoints
        ("POST", "/api/v1/auth/login", None, {"username": "admin", "password": "admin123"}, "Login"),
        ("GET", "/api/v1/auth/me", None, None, "Get current user"),
        
        # Data Query endpoints
        ("GET", "/api/v1/data/pois", None, None, "List all POIs"),
        ("GET", "/api/v1/data/pois", {"city": "hanoi"}, None, "List POIs in Hanoi"),
        ("GET", "/api/v1/data/pois", {"category": "restaurant"}, None, "List restaurants"),
        ("GET", "/api/v1/data/pois/search", {"q": "hotel"}, None, "Search hotels"),
        ("GET", "/api/v1/data/pois/search", {"q": "cafe", "city": "hanoi"}, None, "Search cafes in Hanoi"),
        ("GET", "/api/v1/data/cities", None, None, "List cities"),
        ("GET", "/api/v1/data/categories", None, None, "List categories"),
        
        # Monitoring endpoints
        ("GET", "/health", None, None, "Health check"),
        ("GET", "/ready", None, None, "Readiness check"),
        ("GET", "/api/v1/monitoring/stats", None, None, "Monitoring stats"),
        ("GET", "/api/v1/monitoring/layers", None, None, "Layer info"),
        
        # Pipeline endpoints
        ("GET", "/api/v1/pipeline/status", None, None, "Pipeline status"),
        ("GET", "/api/v1/data/layers", None, None, "Data layers"),
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for method, path, params, data, description in tests:
        print(f"\n{method} {path}")
        if params:
            print(f"  Params: {params}")
        
        result = test_endpoint(method, path, params, data, description)
        results.append(result)
        
        if result["status"] == "✅":
            passed += 1
            print(f"  ✅ {description}")
            if "result" in result and isinstance(result["result"], dict):
                if "total" in result["result"]:
                    print(f"     Total: {result['result']['total']}")
                elif len(str(result["result"])) < 100:
                    print(f"     Result: {result['result']}")
        else:
            failed += 1
            print(f"  ❌ {description}")
            if "error" in result:
                print(f"     Error: {result['error']}")
            if "status_code" in result:
                print(f"     Status: {result['status_code']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 API TEST SUMMARY")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Total: {len(tests)}")
    print(f"   🎯 Success Rate: {passed/len(tests)*100:.1f}%")
    print("\n✅ API testing complete!")


if __name__ == "__main__":
    run_api_tests()
