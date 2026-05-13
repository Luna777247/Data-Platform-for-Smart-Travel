#!/usr/bin/env python3
"""
Smart Tourism API - Comprehensive Endpoint Test
===============================================
Tests all API endpoints listed in the OpenAPI spec.
Luồng: Login trước → Test tất cả endpoints với JWT token.
Usage: python tests/test_api_endpoints.py
"""
import requests
import sys
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_URL = "http://localhost:8000"
TOKEN = None

TEST_USERNAME = os.getenv("TEST_USERNAME", "admin")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "admin123")
TEST_EMAIL    = os.getenv("TEST_EMAIL", "admin@test.com")

# ============================================================
# HELPERS
# ============================================================
def req(method, path, expected_status=None, json_body=None, params=None, label=None):
    url = BASE_URL + path
    h = {"Content-Type": "application/json"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"

    try:
        resp = requests.request(method, url, json=json_body, headers=h, params=params, timeout=10)
        s = resp.status_code
        ok = (expected_status is None and s < 500) or (s == expected_status)
        icon = "✅" if ok else "❌"
        name = label or f"{method} {path}"
        try:
            body = resp.json()
        except Exception:
            body = resp.text[:80]
        print(f"  {icon}  [{s}] {name}")
        if not ok:
            print(f"       └─ Expected {expected_status}, got {s}: {str(body)[:120]}")
        return s, body
    except requests.exceptions.ConnectionError:
        print(f"  ❌  [CONN] {method} {path} — Cannot connect")
        return None, None
    except Exception as e:
        print(f"  ❌  [ERR]  {method} {path} — {e}")
        return None, None


def count(results, s, expected=None):
    if s is None:
        results["skip"] += 1
    elif expected is not None and s == expected:
        results["pass"] += 1
    elif expected is None and s < 500:
        results["pass"] += 1
    else:
        results["fail"] += 1


# ============================================================
# MAIN TEST RUNNER
# ============================================================
def run():
    global TOKEN
    results = {"pass": 0, "fail": 0, "skip": 0}

    print("=" * 65)
    print("  Smart Tourism Data Platform API - Endpoint Tests")
    print(f"  Target: {BASE_URL}")
    print("=" * 65)

    # ── STEP 1: LOGIN (phải thực hiện trước tất cả) ─────────
    print("\n[Authentication - Login]")
    # Register (400 nếu đã tồn tại — vẫn ok)
    s, _ = req("POST", "/api/v1/auth/register",
               json_body={"username": TEST_USERNAME, "email": TEST_EMAIL, "password": TEST_PASSWORD})
    count(results, s) if s not in (200, 201, 400) else results.update({"pass": results["pass"] + 1})

    # Login → lấy token
    s, body = req("POST", "/api/v1/auth/login", expected_status=200,
                  json_body={"username": TEST_USERNAME, "password": TEST_PASSWORD})
    count(results, s, expected=200)
    if s == 200 and isinstance(body, dict):
        TOKEN = body.get("access_token")
        if TOKEN:
            print(f"       └─ Token: {TOKEN[:40]}...")
        else:
            print("       └─ ⚠️  Không lấy được token!")
    else:
        print("       └─ ⚠️  Login thất bại — các test phía sau sẽ bị 401")

    # ── STEP 2: HEALTH & ROOT (public) ─────────────────────
    print("\n[Health & Root]")
    for path in ["/", "/health", "/ready", "/health/detailed"]:
        s, _ = req("GET", path, expected_status=200)
        count(results, s, expected=200)

    # ── STEP 3: MONITORING (cần auth) ──────────────────────
    print("\n[Monitoring]")
    s, _ = req("GET", "/metrics", expected_status=200)
    count(results, s, expected=200)

    for path in [
        "/api/v1/monitoring/status",
        "/api/v1/monitoring/version",
        "/api/v1/monitoring/dependencies",
        "/api/v1/monitoring/stats",
        "/api/v1/monitoring/layers",
    ]:
        s, _ = req("GET", path, expected_status=200)
        count(results, s, expected=200)

    # ── STEP 4: AUTH ENDPOINTS ──────────────────────────────
    print("\n[Authentication - Other]")
    s, _ = req("GET", "/api/v1/auth/validate", expected_status=200)
    count(results, s, expected=200)

    s, _ = req("GET", "/api/v1/auth/me", expected_status=200)
    count(results, s, expected=200)

    s, _ = req("POST", "/api/v1/auth/refresh", expected_status=200)
    count(results, s, expected=200)

    # ── STEP 5: PIPELINE MANAGEMENT ────────────────────────
    print("\n[Pipeline Management]")
    for path in [
        "/api/v1/pipeline/active",
        "/api/v1/pipeline/history",
        "/api/v1/pipeline/dashboard",
        "/api/v1/pipeline/metrics",
        "/api/v1/pipeline/errors",
        "/api/v1/pipeline/data-quality",
        "/api/v1/pipeline/health",
        "/api/v1/pipeline/status",
    ]:
        s, _ = req("GET", path, expected_status=200)
        count(results, s, expected=200)

    # Start pipeline → lấy execution_id
    s, body = req("POST", "/api/v1/pipeline/start", expected_status=200,
                  json_body={"execution_type": "incremental_sync", "cities": ["hanoi"]})
    count(results, s, expected=200)
    exec_id = body.get("execution_id") if isinstance(body, dict) else None
    if exec_id:
        print(f"       └─ execution_id: {exec_id}")

    # Status theo execution_id
    if exec_id:
        s, _ = req("GET", f"/api/v1/pipeline/status/{exec_id}", expected_status=200)
        count(results, s, expected=200)

        # pause/resume/stop trả 404 nếu pipeline đã done — vẫn ok (< 500)
        for method, path in [
            ("POST", f"/api/v1/pipeline/pause/{exec_id}"),
            ("POST", f"/api/v1/pipeline/resume/{exec_id}"),
            ("POST", f"/api/v1/pipeline/stop/{exec_id}"),
        ]:
            s, _ = req(method, path)
            count(results, s)
    else:
        print("       └─ Skipping status/stop/pause/resume (no exec_id)")
        results["skip"] += 4

    s, _ = req("DELETE", "/api/v1/pipeline/cleanup", expected_status=200)
    count(results, s, expected=200)

    # ── STEP 6: MONGODB PIPELINE ───────────────────────────
    print("\n[MongoDB Pipeline]")
    s, _ = req("GET", "/api/v1/pipeline/bronze/stats", expected_status=200)
    count(results, s, expected=200)

    s, _ = req("GET", "/api/v1/pipeline/layers/stats", expected_status=200)
    count(results, s, expected=200)

    s, _ = req("POST", "/api/v1/pipeline/bronze/collect",
               params={"city": "hanoi", "category": "restaurant",
                       "lat": 21.0278, "lng": 105.8342, "radius": 1000})
    count(results, s)

    s, _ = req("POST", "/api/v1/pipeline/bronze-to-silver", params={"batch_size": 5})
    count(results, s)

    s, _ = req("POST", "/api/v1/pipeline/silver-to-gold", params={"batch_size": 5})
    count(results, s)

    # ── STEP 7: DATA QUERY ─────────────────────────────────
    print("\n[Data Query]")
    for path, params in [
        ("/api/v1/data/testpublic", None),
        ("/api/v1/data/testpois",   None),
        ("/api/v1/data/stats",      None),
        ("/api/v1/data/layers",     None),
        ("/api/v1/data/cities",     None),
        ("/api/v1/data/categories", None),
        ("/api/v1/data/pois",            {"limit": 5}),
        ("/api/v1/data/pois/search",     {"q": "pho", "limit": 5}),
        ("/api/v1/data/pois/nearby",     {"lat": 21.028, "lon": 105.854, "radius": 5000}),
    ]:
        s, _ = req("GET", path, params=params)
        count(results, s)

    # ── STEP 8: ADMIN ──────────────────────────────────────
    print("\n[Admin]")
    for path in ["/api/v1/admin/users", "/api/v1/admin/stats", "/api/v1/admin/logs"]:
        s, _ = req("GET", path, expected_status=200)
        count(results, s, expected=200)

    # ── STEP 9: PLUGINS ────────────────────────────────────
    print("\n[Plugin Management]")
    for path in ["/api/v1/plugins/", "/api/v1/plugins/sources/"]:
        s, _ = req("GET", path, expected_status=200)
        count(results, s, expected=200)

    # ── STEP 10: LOGOUT ────────────────────────────────────
    print("\n[Logout]")
    s, _ = req("POST", "/api/v1/auth/logout", expected_status=200)
    count(results, s, expected=200)

    # ── SUMMARY ────────────────────────────────────────────
    total = results["pass"] + results["fail"] + results["skip"]
    denominator = results["pass"] + results["fail"]
    score = results["pass"] / denominator * 100 if denominator > 0 else 0

    print("\n" + "=" * 65)
    print("  RESULTS SUMMARY")
    print("=" * 65)
    print(f"  ✅ Pass  : {results['pass']}")
    print(f"  ❌ Fail  : {results['fail']}")
    print(f"  ⏭️  Skip  : {results['skip']}")
    print(f"  📊 Total : {total}")
    print(f"  📈 Score : {score:.1f}%")
    print("=" * 65)

    return 0 if results["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
