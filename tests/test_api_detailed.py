#!/usr/bin/env python3
"""
Smart Tourism API - Detailed Multi-Case Test Suite
===================================================
Kiểm tra nhiều trường hợp (happy path, edge cases, error cases)
cho từng nhóm API endpoint.
Usage: python tests/test_api_detailed.py
"""
import requests
import sys
import os
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_URL = "http://localhost:8000"
TOKEN = None
RESULTS = {"pass": 0, "fail": 0, "skip": 0}


# ============================================================
# HELPERS
# ============================================================
def req(method, path, expected=None, json_body=None, params=None, token_override=None):
    url = BASE_URL + path
    h = {"Content-Type": "application/json"}
    t = token_override if token_override is not None else TOKEN
    if t:
        h["Authorization"] = f"Bearer {t}"
    try:
        resp = requests.request(method, url, json=json_body, headers=h, params=params, timeout=10)
        return resp.status_code, _body(resp)
    except Exception as e:
        return None, str(e)


def _body(resp):
    try:
        return resp.json()
    except Exception:
        return resp.text[:200]


def check(label, s, body, expected_status, extra_checks=None):
    ok = (s == expected_status)
    if ok and extra_checks:
        for fn, desc in extra_checks:
            if not fn(body):
                ok = False
                print(f"  ❌  [{s}] {label}")
                print(f"       └─ Field check failed: {desc}")
                print(f"       └─ Body: {str(body)[:120]}")
                RESULTS["fail"] += 1
                return
    icon = "✅" if ok else "❌"
    print(f"  {icon}  [{s}] {label}")
    if not ok:
        print(f"       └─ Expected {expected_status}, got {s}: {str(body)[:120]}")
    RESULTS["pass" if ok else "fail"] += 1


def section(title):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


# ============================================================
# 1. AUTH TESTS
# ============================================================
def test_auth():
    global TOKEN
    section("AUTH — Login / Register / Token")

    # 1.1 Login đúng credentials
    s, body = req("POST", "/api/v1/auth/login",
                  json_body={"username": "admin", "password": "admin123"})
    check("Login với credentials đúng → 200", s, body, 200, [
        (lambda b: isinstance(b, dict) and "access_token" in b, "access_token phải có trong response"),
        (lambda b: isinstance(b, dict) and b.get("token_type") == "bearer", "token_type phải là 'bearer'"),
    ])
    if s == 200 and isinstance(body, dict):
        TOKEN = body.get("access_token")

    # 1.2 Login sai password
    s, body = req("POST", "/api/v1/auth/login",
                  json_body={"username": "admin", "password": "wrongpass"})
    check("Login sai password → 401", s, body, 401)

    # 1.3 Login user không tồn tại
    s, body = req("POST", "/api/v1/auth/login",
                  json_body={"username": "nonexistent_xyz", "password": "anypass"})
    check("Login user không tồn tại → 401", s, body, 401)

    # 1.4 Login thiếu password field
    s, body = req("POST", "/api/v1/auth/login",
                  json_body={"username": "admin"})
    check("Login thiếu password → 422", s, body, 422)

    # 1.5 Login body rỗng
    s, body = req("POST", "/api/v1/auth/login", json_body={})
    check("Login body rỗng → 422", s, body, 422)

    # 1.6 Register user mới (unique name)
    new_user = f"testuser_{int(time.time())}"
    s, body = req("POST", "/api/v1/auth/register",
                  json_body={"username": new_user, "email": f"{new_user}@test.com", "password": "Test@1234"})
    check("Register user mới → 200/201", s, body, 200)

    # 1.7 Register user trùng tên
    s, body = req("POST", "/api/v1/auth/register",
                  json_body={"username": "admin", "email": "admin@test.com", "password": "admin123"})
    check("Register user đã tồn tại → 400", s, body, 400)

    # 1.8 Register thiếu field
    s, body = req("POST", "/api/v1/auth/register",
                  json_body={"username": "onlyname"})
    check("Register thiếu email/password → 422", s, body, 422)

    # 1.9 GET /me với token hợp lệ
    s, body = req("GET", "/api/v1/auth/me")
    check("GET /auth/me với token → 200", s, body, 200, [
        (lambda b: isinstance(b, dict) and "username" in b, "username phải có"),
    ])

    # 1.10 GET /me không có token
    s, body = req("GET", "/api/v1/auth/me", token_override="")
    check("GET /auth/me không có token → 401/403", s, body, 401)

    # 1.11 GET /me token giả
    s, body = req("GET", "/api/v1/auth/me", token_override="fake.token.here")
    check("GET /auth/me token giả → 401/403", s, body, 401)

    # 1.12 Validate token hợp lệ
    s, body = req("GET", "/api/v1/auth/validate")
    check("Validate token hợp lệ → 200", s, body, 200)

    # 1.13 Refresh token
    s, body = req("POST", "/api/v1/auth/refresh")
    check("Refresh token → 200", s, body, 200, [
        (lambda b: isinstance(b, dict) and "access_token" in b, "access_token phải có"),
    ])

    # 1.14 Logout
    s, body = req("POST", "/api/v1/auth/logout")
    check("Logout → 200", s, body, 200)


# ============================================================
# 2. PIPELINE MANAGEMENT TESTS
# ============================================================
def test_pipeline():
    section("PIPELINE MANAGEMENT — Lifecycle & Status")

    # 2.1 Start pipeline với đúng payload
    s, body = req("POST", "/api/v1/pipeline/start",
                  json_body={"execution_type": "incremental_sync", "cities": ["hanoi"]})
    check("Start pipeline incremental_sync → 200", s, body, 200, [
        (lambda b: isinstance(b, dict) and "execution_id" in b, "execution_id phải có"),
        (lambda b: isinstance(b, dict) and b.get("status") == "started", "status phải là 'started'"),
    ])
    exec_id = body.get("execution_id") if isinstance(body, dict) else None

    # 2.2 Start pipeline full_sync
    s, body = req("POST", "/api/v1/pipeline/start",
                  json_body={"execution_type": "full_sync"})
    check("Start pipeline full_sync (no cities) → 200", s, body, 200)
    exec_id2 = body.get("execution_id") if isinstance(body, dict) else None

    # 2.3 Start pipeline thiếu execution_type
    s, body = req("POST", "/api/v1/pipeline/start",
                  json_body={"cities": ["hanoi"]})
    check("Start pipeline thiếu execution_type → 422", s, body, 422)

    # 2.4 Start pipeline execution_type không hợp lệ
    s, body = req("POST", "/api/v1/pipeline/start",
                  json_body={"execution_type": "invalid_type"})
    check("Start pipeline execution_type không hợp lệ → 422", s, body, 422)

    # 2.5 Get status pipeline vừa start
    if exec_id:
        s, body = req("GET", f"/api/v1/pipeline/status/{exec_id}")
        check(f"Get status pipeline {exec_id[:20]}... → 200", s, body, 200, [
            (lambda b: isinstance(b, dict) and "status" in b, "status phải có"),
            (lambda b: isinstance(b, dict) and "execution_id" in b, "execution_id phải có"),
            (lambda b: isinstance(b, dict) and "progress" in b, "progress phải có"),
        ])

    # 2.6 Get status pipeline ID không tồn tại
    s, body = req("GET", "/api/v1/pipeline/status/nonexistent_pipeline_id_xyz")
    check("Get status pipeline không tồn tại → 404", s, body, 404)

    # 2.7 Pause pipeline đã done (404 expected)
    if exec_id:
        s, body = req("POST", f"/api/v1/pipeline/pause/{exec_id}")
        check(f"Pause pipeline đã done → 404", s, body, 404)

    # 2.8 Stop pipeline đã done (404 expected)
    if exec_id:
        s, body = req("POST", f"/api/v1/pipeline/stop/{exec_id}")
        check(f"Stop pipeline đã done → 404", s, body, 404)

    # 2.9 Resume pipeline đã done (404 expected)
    if exec_id:
        s, body = req("POST", f"/api/v1/pipeline/resume/{exec_id}")
        check(f"Resume pipeline đã done → 404", s, body, 404)

    # 2.10 GET /active — danh sách pipeline đang chạy
    s, body = req("GET", "/api/v1/pipeline/active")
    check("GET /pipeline/active → 200 (list)", s, body, 200, [
        (lambda b: isinstance(b, list), "phải trả về array"),
    ])

    # 2.11 GET /history với limit
    s, body = req("GET", "/api/v1/pipeline/history", params={"limit": 5})
    check("GET /pipeline/history?limit=5 → 200", s, body, 200)

    # 2.12 GET /dashboard
    s, body = req("GET", "/api/v1/pipeline/dashboard")
    check("GET /pipeline/dashboard → 200", s, body, 200, [
        (lambda b: isinstance(b, dict), "phải trả về object"),
    ])

    # 2.13 GET /metrics
    s, body = req("GET", "/api/v1/pipeline/metrics")
    check("GET /pipeline/metrics → 200", s, body, 200)

    # 2.14 GET /errors
    s, body = req("GET", "/api/v1/pipeline/errors")
    check("GET /pipeline/errors → 200", s, body, 200)

    # 2.15 GET /data-quality
    s, body = req("GET", "/api/v1/pipeline/data-quality")
    check("GET /pipeline/data-quality → 200", s, body, 200)

    # 2.16 GET /health
    s, body = req("GET", "/api/v1/pipeline/health")
    check("GET /pipeline/health → 200", s, body, 200)

    # 2.17 DELETE /cleanup
    s, body = req("DELETE", "/api/v1/pipeline/cleanup")
    check("DELETE /pipeline/cleanup → 200", s, body, 200)

    # 2.18 GET /pipeline/status (System Status)
    s, body = req("GET", "/api/v1/pipeline/status")
    check("GET /pipeline/status → 200", s, body, 200)

    # 2.19 POST /pipeline/restart
    if exec_id:
        s, body = req("POST", f"/api/v1/pipeline/restart/{exec_id}")
        check(f"POST /pipeline/restart {exec_id[:20]}... → 200", s, body, 200)

    # 2.20 Pipeline không có auth
    s, body = req("GET", "/api/v1/pipeline/active", token_override="")
    check("GET /pipeline/active không có token → 401", s, body, 401)


# ============================================================
# 3. MONGODB PIPELINE TESTS
# ============================================================
def test_mongodb_pipeline():
    section("MONGODB PIPELINE — Bronze / Silver / Gold")

    # 3.1 Bronze stats
    s, body = req("GET", "/api/v1/pipeline/bronze/stats")
    check("GET /bronze/stats → 200", s, body, 200, [
        (lambda b: isinstance(b, dict), "phải trả về object"),
    ])

    # 3.2 Layers stats
    s, body = req("GET", "/api/v1/pipeline/layers/stats")
    check("GET /layers/stats → 200", s, body, 200)

    # 3.3 Bronze collect đúng params
    s, body = req("POST", "/api/v1/pipeline/bronze/collect",
                  params={"city": "hanoi", "category": "restaurant",
                          "lat": 21.0278, "lng": 105.8342, "radius": 1000})
    check("POST /bronze/collect (hanoi/restaurant) → 200", s, body, 200)

    # 3.4 Bronze collect city khác
    s, body = req("POST", "/api/v1/pipeline/bronze/collect",
                  params={"city": "hcm", "category": "hotel",
                          "lat": 10.7769, "lng": 106.7009, "radius": 2000})
    check("POST /bronze/collect (hcm/hotel) → 200", s, body, 200)

    # 3.5 Bronze collect thiếu city
    s, body = req("POST", "/api/v1/pipeline/bronze/collect",
                  params={"category": "restaurant", "lat": 21.0, "lng": 105.8, "radius": 1000})
    check("POST /bronze/collect thiếu city → 422", s, body, 422)

    # 3.6 Bronze-to-silver với batch_size nhỏ
    s, body = req("POST", "/api/v1/pipeline/bronze-to-silver", params={"batch_size": 2})
    check("POST /bronze-to-silver batch_size=2 → 200", s, body, 200)

    # 3.7 Bronze-to-silver batch_size lớn
    s, body = req("POST", "/api/v1/pipeline/bronze-to-silver", params={"batch_size": 100})
    check("POST /bronze-to-silver batch_size=100 → 200", s, body, 200)

    # 3.8 Silver-to-gold
    s, body = req("POST", "/api/v1/pipeline/silver-to-gold", params={"batch_size": 5})
    check("POST /silver-to-gold batch_size=5 → 200", s, body, 200)

    # 3.9 Bronze mass collect
    s, body = req("POST", "/api/v1/pipeline/bronze/mass-collect",
                  params={"cities": ["hanoi", "hcm"], "categories": ["hotel"]})
    check("POST /bronze/mass-collect → 200", s, body, 200)

    # 3.10 Run full pipeline
    s, body = req("POST", "/api/v1/pipeline/run-full-pipeline",
                  params={"cities": ["hanoi"], "categories": ["restaurant"]})
    check("POST /run-full-pipeline → 200", s, body, 200)

    # 3.11 Không có auth
    s, body = req("GET", "/api/v1/pipeline/bronze/stats", token_override="")
    check("GET /bronze/stats không có token → 401", s, body, 401)


# ============================================================
# 4. DATA QUERY TESTS
# ============================================================
def test_data_query():
    section("DATA QUERY — POIs / Search / Nearby / Stats")

    # 4.1 List POIs mặc định
    s, body = req("GET", "/api/v1/data/pois")
    check("GET /data/pois (no params) → 200", s, body, 200, [
        (lambda b: isinstance(b, dict) and "items" in b, "phải có 'items'"),
        (lambda b: isinstance(b, dict) and "total" in b, "phải có 'total'"),
    ])

    # 4.2 List POIs với limit
    s, body = req("GET", "/api/v1/data/pois", params={"limit": 3})
    check("GET /data/pois?limit=3 → 200", s, body, 200, [
        (lambda b: isinstance(b, dict) and len(b.get("items", [])) <= 3, "items <= 3"),
    ])

    # 4.3 List POIs với page
    s, body = req("GET", "/api/v1/data/pois", params={"limit": 5, "skip": 0})
    check("GET /data/pois?limit=5&skip=0 → 200", s, body, 200)

    # 4.4 List POIs filter theo city
    s, body = req("GET", "/api/v1/data/pois", params={"city": "hanoi", "limit": 5})
    check("GET /data/pois?city=hanoi → 200", s, body, 200)

    # 4.5 List POIs filter theo layer
    s, body = req("GET", "/api/v1/data/pois", params={"layer": "gold", "limit": 5})
    check("GET /data/pois?layer=gold → 200", s, body, 200)

    # 4.6 Search POIs keyword
    s, body = req("GET", "/api/v1/data/pois/search", params={"q": "pho", "limit": 5})
    check("GET /pois/search?q=pho → 200", s, body, 200)

    # 4.7 Search POIs keyword rỗng
    s, body = req("GET", "/api/v1/data/pois/search", params={"q": "", "limit": 5})
    check("GET /pois/search?q= (rỗng) → 200/422", s, body, 200)

    # 4.8 Search POIs thiếu q param
    s, body = req("GET", "/api/v1/data/pois/search")
    check("GET /pois/search không có q → 422", s, body, 422)

    # 4.9 Nearby POIs với coords hợp lệ
    s, body = req("GET", "/api/v1/data/pois/nearby",
                  params={"lat": 21.028, "lon": 105.854, "radius": 5000})
    check("GET /pois/nearby (Hà Nội) → 200", s, body, 200, [
        (lambda b: isinstance(b, dict) and "items" in b, "phải có 'items'"),
    ])

    # 4.10 Nearby với radius lớn
    s, body = req("GET", "/api/v1/data/pois/nearby",
                  params={"lat": 10.776, "lon": 106.700, "radius": 10000})
    check("GET /pois/nearby (HCM, radius=10km) → 200", s, body, 200)

    # 4.11 Nearby thiếu lat/lon
    s, body = req("GET", "/api/v1/data/pois/nearby", params={"radius": 1000})
    check("GET /pois/nearby thiếu lat/lon → 422", s, body, 422)

    # 4.12 Get POI theo ID (Success Case)
    poi_id = None
    s_list, body_list = req("GET", "/api/v1/data/pois", params={"limit": 1})
    
    # Fallback to bronze layer if gold is empty
    if s_list == 200 and isinstance(body_list, dict) and not body_list.get("items"):
        print("  ℹ️  Default layer empty, trying bronze layer for test POI...")
        s_list, body_list = req("GET", "/api/v1/data/pois", params={"limit": 1, "layer": "bronze"})

    if s_list == 200 and isinstance(body_list, dict) and body_list.get("items"):
        poi_item = body_list["items"][0]
        poi_id = poi_item.get("poi_id") or poi_item.get("id") or poi_item.get("_id")
    
    if poi_id:
        s, body = req("GET", f"/api/v1/data/pois/{poi_id}")
        check(f"GET /pois/{{id}} hợp lệ → 200", s, body, 200)
    else:
        print("  ⏭️  [SKIP] GET /pois/{id} 200 test — không tìm thấy POI mẫu")
        RESULTS["skip"] += 1

    # 4.13 Get POI theo ID không tồn tại
    s, body = req("GET", "/api/v1/data/pois/nonexistent_poi_id_xyz_123")
    check("GET /pois/{id} không tồn tại → 404", s, body, 404)

    # 4.14 Test endpoints
    s, body = req("GET", "/api/v1/data/testpois")
    check("GET /data/testpois → 200", s, body, 200)

    s, body = req("GET", "/api/v1/data/testpublic")
    check("GET /data/testpublic (public) → 200", s, body, 200)

    # 4.15 Stats
    s, body = req("GET", "/api/v1/data/stats")
    check("GET /data/stats → 200", s, body, 200, [
        (lambda b: isinstance(b, dict), "phải trả về object"),
    ])

    # 4.14 Layers info
    s, body = req("GET", "/api/v1/data/layers")
    check("GET /data/layers → 200", s, body, 200, [
        (lambda b: isinstance(b, list), "phải trả về array"),
    ])

    # 4.15 Cities list
    s, body = req("GET", "/api/v1/data/cities")
    check("GET /data/cities → 200 (list string)", s, body, 200, [
        (lambda b: isinstance(b, list), "phải trả về array"),
    ])

    # 4.16 Categories list
    s, body = req("GET", "/api/v1/data/categories")
    check("GET /data/categories → 200 (list string)", s, body, 200, [
        (lambda b: isinstance(b, list), "phải trả về array"),
    ])

    # 4.17 POIs không có auth
    s, body = req("GET", "/api/v1/data/pois", token_override="")
    check("GET /data/pois không có token → 401", s, body, 401)


# ============================================================
# 5. MONITORING TESTS
# ============================================================
def test_monitoring():
    section("MONITORING — Status / Version / Dependencies")

    # 5.1 Public metrics
    s, body = req("GET", "/metrics")
    check("GET /metrics (public) → 200", s, body, 200)

    # 5.2 Status với auth
    s, body = req("GET", "/api/v1/monitoring/status")
    check("GET /monitoring/status (auth) → 200", s, body, 200)

    # 5.3 Version
    s, body = req("GET", "/api/v1/monitoring/version")
    check("GET /monitoring/version → 200", s, body, 200)

    # 5.4 Dependencies
    s, body = req("GET", "/api/v1/monitoring/dependencies")
    check("GET /monitoring/dependencies → 200", s, body, 200)

    # 5.5 Stats
    s, body = req("GET", "/api/v1/monitoring/stats")
    check("GET /monitoring/stats → 200", s, body, 200)

    # 5.6 Layers
    s, body = req("GET", "/api/v1/monitoring/layers")
    check("GET /monitoring/layers → 200", s, body, 200)

    # 5.7 Không có auth → 401
    s, body = req("GET", "/api/v1/monitoring/status", token_override="")
    check("GET /monitoring/status không có token → 401", s, body, 401)

    # 5.8 Token giả → 401
    s, body = req("GET", "/api/v1/monitoring/status", token_override="invalid.jwt.token")
    check("GET /monitoring/status token giả → 401", s, body, 401)


# ============================================================
# 6. ADMIN TESTS
# ============================================================
def test_admin():
    section("ADMIN — Users / Stats / Logs")

    # 6.1 List users
    s, body = req("GET", "/api/v1/admin/users")
    check("GET /admin/users → 200", s, body, 200)

    # 6.2 Stats
    s, body = req("GET", "/api/v1/admin/stats")
    check("GET /admin/stats → 200", s, body, 200)

    # 6.3 Logs
    s, body = req("GET", "/api/v1/admin/logs")
    check("GET /admin/logs → 200", s, body, 200)

    # 6.4 Create new user via Admin
    admin_user = f"admin_test_{int(time.time())}"
    s, body = req("POST", "/api/v1/admin/users",
                  json_body={"username": admin_user, "email": f"{admin_user}@admin.com", "password": "AdminPassword123", "role": "admin"})
    check("POST /admin/users → 201", s, body, 201)
    created_user_id = body.get("id") if isinstance(body, dict) else None

    # 6.5 Delete user via Admin
    if created_user_id:
        s, body = req("DELETE", f"/api/v1/admin/users/{created_user_id}")
        check("DELETE /admin/users/{id} → 204", s, body, 204)

    # 6.6 Maintenance mode
    s, body = req("POST", "/api/v1/admin/maintenance", json_body={"enabled": True})
    check("POST /admin/maintenance (enable) → 200", s, body, 200)
    req("POST", "/api/v1/admin/maintenance", json_body={"enabled": False}) # Restore

    # 6.7 Cleanup
    s, body = req("POST", "/api/v1/admin/cleanup")
    check("POST /admin/cleanup → 200", s, body, 200)

    # 6.8 Không có auth
    s, body = req("GET", "/api/v1/admin/users", token_override="")
    check("GET /admin/users không có token → 401/403", s, body, 401)

    # 6.5 Auth với user thường (non-admin) → 403
    # Đăng nhập bằng testuser (role=user)
    ls, lbody = req("POST", "/api/v1/auth/login",
                    json_body={"username": "testuser", "password": "test123"})
    if ls == 200 and isinstance(lbody, dict):
        user_token = lbody.get("access_token")
        s, body = req("GET", "/api/v1/admin/users", token_override=user_token)
        check("GET /admin/users với user thường → 403", s, body, 403)
    else:
        print("  ⏭️  [SKIP] Admin 403 test — testuser không login được")
        RESULTS["skip"] += 1


# ============================================================
# 7. HEALTH TESTS
# ============================================================
def test_health():
    section("HEALTH — Public Endpoints")

    # 7.1 Root
    s, body = req("GET", "/")
    check("GET / → 200", s, body, 200)

    # 7.2 /health
    s, body = req("GET", "/health")
    check("GET /health → 200", s, body, 200, [
        (lambda b: isinstance(b, dict) and b.get("status") in ("healthy", "ok", "running"),
         "status phải là healthy/ok/running"),
    ])

    # 7.3 /ready
    s, body = req("GET", "/ready")
    check("GET /ready → 200", s, body, 200)

    # 7.4 /health/detailed
    s, body = req("GET", "/health/detailed")
    check("GET /health/detailed → 200", s, body, 200)

    # 7.5 Route không tồn tại → 404
    s, body = req("GET", "/api/v1/notexist")
    check("GET /api/v1/notexist → 404", s, body, 404)


# ============================================================
# 8. PLUGIN TESTS
# ============================================================
def test_plugins():
    section("PLUGINS")
    # 8.1 List Plugins
    s, body = req("GET", "/api/v1/plugins/")
    check("GET /plugins/ → 200", s, body, 200)

    # 8.2 Register Plugin
    plugin_id_val = f"test_plugin_{int(time.time())}"
    s, body = req("POST", "/api/v1/plugins/", 
                  json_body={
                      "plugin_id": plugin_id_val,
                      "plugin_type": "source",
                      "name": "Test Plugin",
                      "description": "Test plugin for API testing",
                      "version": "1.0.0",
                      "class_path": "src.collectors.osm_collector.OSMCollector"
                  })
    check("POST /plugins/ → 200", s, body, 200)
    plugin_id = body.get("plugin_id") if isinstance(body, dict) else None

    # 8.3 Get Plugin detail
    if plugin_id:
        s, body = req("GET", f"/api/v1/plugins/{plugin_id}")
        check(f"GET /plugins/{{id}} → 200", s, body, 200)
        
        # 8.4 Test Plugin
        s, body = req("POST", f"/api/v1/plugins/{plugin_id}/test")
        check(f"POST /plugins/{{id}}/test → 200", s, body, 200)

    # 8.5 List Sources
    s, body = req("GET", "/api/v1/plugins/sources/")
    check("GET /plugins/sources/ → 200", s, body, 200)

    # 8.6 Create Source
    source_id_val = f"src_{int(time.time())}"
    # Dùng plugin_id vừa tạo hoặc một plugin mặc định (ví dụ: 'osm')
    target_plugin = plugin_id or "osm" 
    s, body = req("POST", "/api/v1/plugins/sources/", 
                  json_body={
                      "source_id": source_id_val,
                      "plugin_id": target_plugin,
                      "name": "Test Source",
                      "config": {"api_key": "test_key"}
                  })
    check("POST /plugins/sources/ → 200", s, body, 200)
    source_id = body.get("source_id") if isinstance(body, dict) else None

    # 8.7 Trigger Collect from source
    if source_id:
        s, body = req("POST", f"/api/v1/plugins/sources/{source_id}/collect",
                      params={"city": "hanoi", "category": "restaurant"})
        check(f"POST /plugins/sources/{{id}}/collect → 200", s, body, 200)

    # 8.8 Unregister Plugin
    if plugin_id:
        s, body = req("DELETE", f"/api/v1/plugins/{plugin_id}")
        check("DELETE /plugins/{{id}} → 200", s, body, 200)


# ============================================================
# MAIN
# ============================================================
def run():
    print("=" * 65)
    print("  Smart Tourism API — Detailed Multi-Case Test Suite")
    print(f"  Target: {BASE_URL}")
    print("=" * 65)

    # Login trước để lấy token
    s, body = req("POST", "/api/v1/auth/login",
                  json_body={"username": "admin", "password": "admin123"})
    global TOKEN
    if s == 200 and isinstance(body, dict):
        TOKEN = body.get("access_token")
        if TOKEN:
            print(f"\n  🔑 Token acquired: {TOKEN[:40]}...")
        else:
            print(f"\n  ⚠️  Login success but no access_token found!")
    else:
        print(f"\n  ⚠️  Login failed ({s}) — nhiều test sẽ fail!")

    # Chạy từng nhóm test
    test_health()
    test_auth()
    test_monitoring()
    test_pipeline()
    test_mongodb_pipeline()
    test_data_query()
    test_admin()
    test_plugins()

    # Summary
    total = RESULTS["pass"] + RESULTS["fail"] + RESULTS["skip"]
    denominator = RESULTS["pass"] + RESULTS["fail"]
    score = RESULTS["pass"] / denominator * 100 if denominator > 0 else 0

    print("\n" + "=" * 65)
    print("  DETAILED TEST RESULTS SUMMARY")
    print("=" * 65)
    print(f"  ✅ Pass  : {RESULTS['pass']}")
    print(f"  ❌ Fail  : {RESULTS['fail']}")
    print(f"  ⏭️  Skip  : {RESULTS['skip']}")
    print(f"  📊 Total : {total}")
    print(f"  📈 Score : {score:.1f}%")
    print("=" * 65)

    return 0 if RESULTS["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
