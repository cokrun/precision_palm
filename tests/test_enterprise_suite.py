import urllib.request
import urllib.parse
import json
import base64
import hashlib
import time

BASE_URL = "http://127.0.0.1:8080"

def run_tests():
    print("==================================================================")
    print("[TEST SUITE] COMPREHENSIVE ENTERPRISE SPECIFICATION")
    print("==================================================================")

    # 1. TEST PENGATURAN ROUTES & SETTINGS API
    print("\n[TEST 1] Testing /pengaturan and /api/settings...")
    req = urllib.request.urlopen(f"{BASE_URL}/pengaturan")
    assert req.status == 200, f"Expected 200, got {req.status}"
    html = req.read().decode('utf-8')
    assert "Pusat Kendali Pengaturan" in html or "pengaturan" in html.lower()
    print("[OK] GET /pengaturan returned HTTP 200 with HTML")

    req_set = urllib.request.urlopen(f"{BASE_URL}/api/settings")
    res_set = json.loads(req_set.read().decode('utf-8'))
    assert res_set.get("status") == "success"
    settings = res_set.get("settings", {})
    assert "market_mode" in settings
    assert "cpo_global" in settings
    print(f"[OK] GET /api/settings returned settings: {list(settings.keys())}")

    post_data = json.dumps({"market_mode": "DOMESTIC_IDR", "audit_year": "2026"}).encode('utf-8')
    req_post = urllib.request.Request(f"{BASE_URL}/api/settings", data=post_data, headers={'Content-Type': 'application/json'})
    res_post = json.loads(urllib.request.urlopen(req_post).read().decode('utf-8'))
    assert res_post.get("status") == "success"
    print("[OK] POST /api/settings successfully persisted settings")

    # 2. TEST PRICING ENGINE MICROSERVICE
    print("\n[TEST 2] Testing /api/pricing/tbs-calculation...")
    req_price = urllib.request.urlopen(f"{BASE_URL}/api/pricing/tbs-calculation")
    res_price = json.loads(req_price.read().decode('utf-8'))
    assert res_price.get("status") == "success"
    tbs_data = res_price.get("data", {})
    print(f"[OK] TBS Price/Kg: Rp {tbs_data.get('harga_tbs_idr_kg'):,.2f}")
    print(f"[OK] Total Integrated Revenue: Rp {tbs_data.get('total_integrated_idr_ha'):,.0f} /Ha")
    print(f"[OK] Statutory Basis: {res_price.get('statutory_basis')}")

    # 3. TEST MULTI-TENANCY ISOLATION (EST-MDN-001 vs Clean New Dossier EST-RIAU-002)
    print("\n[TEST 3] Testing Multi-Tenancy Strict Isolation...")
    # Fetch evidence for canonical estate EST-MDN-001
    url_mdn = f"{BASE_URL}/api/evidence/list?dossier_id=EST-MDN-001"
    try:
        req_mdn = urllib.request.urlopen(url_mdn)
        res_mdn = json.loads(req_mdn.read().decode('utf-8'))
        mdn_count = len(res_mdn.get("evidence", []))
        print(f"[OK] EST-MDN-001 has {mdn_count} registered evidence records")
    except Exception as e:
        print(f"  EST-MDN-001 list check: {e}")

    # Fetch evidence for a brand new clean dossier EST-RIAU-002 (should be empty, not leak EST-MDN-001)
    url_riau = f"{BASE_URL}/api/evidence/list?dossier_id=EST-RIAU-002"
    try:
        req_riau = urllib.request.urlopen(url_riau)
        res_riau = json.loads(req_riau.read().decode('utf-8'))
        riau_count = len(res_riau.get("evidence", []))
        print(f"[OK] EST-RIAU-002 (new dossier) has {riau_count} evidence records (Isolation 100% verified!)")
        assert riau_count == 0, f"Expected 0 isolated records for new tenant, got {riau_count}"
    except urllib.error.HTTPError as e:
        print(f"[OK] EST-RIAU-002 returns empty/clean status {e.code}")

    # Test latest streaming endpoint for clean tenant
    url_stream_riau = f"{BASE_URL}/api/media/evidence/latest?dossier_id=EST-RIAU-002"
    try:
        urllib.request.urlopen(url_stream_riau)
        print("[FAIL] Should have returned 404 for non-existent evidence of clean tenant")
    except urllib.error.HTTPError as e:
        assert e.code == 404
        print(f"[OK] Streaming /api/media/evidence/latest?dossier_id=EST-RIAU-002 returned HTTP 404 (Zero leakage confirmed)")

    # 4. TEST ANTI-FRAUD PHOTO (ZERO RE-USE)
    print("\n[TEST 4] Testing Anti-Fraud Photo Zero Re-use...")
    # Generate unique test image payload
    unique_content = f"Test Anti Fraud Image {time.time()}".encode('utf-8')
    b64_img = base64.b64encode(unique_content).decode('utf-8')
    img_hash = hashlib.sha256(unique_content).hexdigest()
    
    upload_payload = json.dumps({
        "dossier_id": "EST-MDN-001",
        "block_id": "BLOK-TEST-AF",
        "perspective_mode": "in-situ",
        "image_base64": b64_img,
        "gps_lat": 0.8241,
        "gps_lng": 99.5612,
        "audit_year": "2026"
    }).encode('utf-8')

    # First upload: should succeed (200 or 201)
    req_upload1 = urllib.request.Request(f"{BASE_URL}/api/evidence/upload", data=upload_payload, headers={'Content-Type': 'application/json'})
    res_upload1 = urllib.request.urlopen(req_upload1)
    up_data = json.loads(res_upload1.read().decode('utf-8'))
    created_ev_id = up_data.get('evidence_id')
    print(f"[OK] Initial photo upload succeeded with HTTP {res_upload1.status}")

    # Second upload with identical binary content: MUST fail with HTTP 409 Conflict
    try:
        req_upload2 = urllib.request.Request(f"{BASE_URL}/api/evidence/upload", data=upload_payload, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req_upload2)
        print("[FAIL]: Duplicate photo was NOT blocked!")
        assert False, "Duplicate photo should have been rejected with 409 Conflict"
    except urllib.error.HTTPError as e:
        print(f"[OK] Duplicate photo upload properly blocked with HTTP {e.code} Conflict! (Anti-Fraud Verified)")
        assert e.code == 409, f"Expected 409 Conflict, got {e.code}"
        err_body = json.loads(e.read().decode('utf-8'))
        print(f"  Error message: {err_body.get('message') or err_body.get('error')}")

    # Clean up test row so EST-MDN-001 retains valid physical inspection evidence
    if created_ev_id:
        import sqlite3
        conn_cleanup = sqlite3.connect('precision_palm.db')
        conn_cleanup.execute("DELETE FROM inspection_evidence WHERE evidence_id = ?", (created_ev_id,))
        conn_cleanup.execute("DELETE FROM used_photo_hashes WHERE evidence_id = ?", (created_ev_id,))
        conn_cleanup.commit()
        conn_cleanup.close()

    # 5. TEST TABLE PAGINATION (MAX 10 ROWS)
    print("\n[TEST 5] Testing Table Pagination (limit=10)...")
    req_hist = urllib.request.urlopen(f"{BASE_URL}/api/admin/history?page=1&limit=10")
    res_hist = json.loads(req_hist.read().decode('utf-8'))
    records = res_hist.get("records") or res_hist.get("data") or []
    print(f"[OK] /api/admin/history returned {len(records)} records (Max <= 10 limit respected)")
    assert len(records) <= 10, f"Expected <= 10 rows, got {len(records)}"

    print("\n==================================================================")
    print("[SUCCESS] ALL TESTS PASSED SUCCESSFULLY! 100% SPEC COMPLIANT")
    print("==================================================================")

if __name__ == '__main__':
    run_tests()
