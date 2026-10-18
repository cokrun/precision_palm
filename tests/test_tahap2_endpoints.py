import urllib.request
import urllib.parse
import urllib.error
import json
import base64
import hashlib
import time
import sys

# Ensure UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8080"

def run_all_tahap2_tests():
    print("=" * 70)
    print("🧪 MEMULAI PENGUJIAN 7 ENDPOINT TAHAP 2 (SQLITE WAL MURNI)")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. TEST /pengaturan & /api/settings
    # -------------------------------------------------------------
    print("\n[TEST 1/7] GET /pengaturan & GET/POST /api/settings")
    req_ui = urllib.request.urlopen(f"{BASE_URL}/pengaturan")
    assert req_ui.status == 200, f"Expected 200 for /pengaturan, got {req_ui.status}"
    ui_html = req_ui.read().decode('utf-8')
    assert "pengaturan" in ui_html.lower() or "settings" in ui_html.lower()
    print("  ✅ GET /pengaturan berhasil mengembalikan HTTP 200 (HTML UI)")

    req_set = urllib.request.urlopen(f"{BASE_URL}/api/settings")
    assert req_set.status == 200
    res_set = json.loads(req_set.read().decode('utf-8'))
    assert res_set.get("status") == "success"
    settings = res_set.get("settings", {})
    print(f"  ✅ GET /api/settings berhasil: {len(settings)} parameter sistem termuat")

    post_payload = json.dumps({"market_mode": "DOMESTIC_IDR", "tahap2_test_key": "verified_wal"}).encode('utf-8')
    req_post_set = urllib.request.Request(f"{BASE_URL}/api/settings", data=post_payload, headers={'Content-Type': 'application/json'})
    res_post_set = json.loads(urllib.request.urlopen(req_post_set).read().decode('utf-8'))
    assert res_post_set.get("status") == "success"
    print("  ✅ POST /api/settings berhasil memperbarui parameter konfigurasi")

    # -------------------------------------------------------------
    # 2. TEST POST /api/dossier/register
    # -------------------------------------------------------------
    print("\n[TEST 2/7] POST /api/dossier/register")
    unique_suffix = int(time.time())
    new_company_id = f"COMP-RIAU-{unique_suffix % 10000}"
    new_dossier_id = f"EST-RIAU-{unique_suffix % 10000}"
    reg_payload = json.dumps({
        "company_id": new_company_id,
        "company_name": f"PT Riau Sawit Lestari {unique_suffix}",
        "tax_id": f"NPWP-99.{unique_suffix % 1000}.456",
        "dossier_id": new_dossier_id,
        "estate_name": f"Estate Riau Makmur {unique_suffix % 1000}",
        "hectares_declared": 2500.5,
        "region_code": "RIAU-01",
        "target_certification": "RSPO/ISPO"
    }).encode('utf-8')

    req_reg = urllib.request.Request(f"{BASE_URL}/api/dossier/register", data=reg_payload, headers={'Content-Type': 'application/json'})
    res_reg = urllib.request.urlopen(req_reg)
    assert res_reg.status in [200, 201]
    res_reg_json = json.loads(res_reg.read().decode('utf-8'))
    assert res_reg_json.get("status") == "success"
    print(f"  ✅ POST /api/dossier/register berhasil: Company={new_company_id}, Dossier={new_dossier_id}")

    # -------------------------------------------------------------
    # 3. TEST GET /api/dossier/<dossier_id>/state
    # -------------------------------------------------------------
    print("\n[TEST 3/7] GET /api/dossier/<dossier_id>/state")
    # Test Empty State for the freshly registered dossier (or EST-RIAU-002)
    req_state_empty = urllib.request.urlopen(f"{BASE_URL}/api/dossier/EST-RIAU-002/state")
    assert req_state_empty.status == 200
    state_empty_json = json.loads(req_state_empty.read().decode('utf-8'))
    assert state_empty_json.get("status") == "success"
    print(f"  ✅ GET /api/dossier/EST-RIAU-002/state: estate={state_empty_json.get('dossier', {}).get('estate_block_name')}, telemetry={state_empty_json.get('telemetry') is not None}, evidence={state_empty_json.get('latest_evidence') is not None} (Clean Empty State)")

    # Test State for seeded active dossier EST-MDN-001
    req_state_mdn = urllib.request.urlopen(f"{BASE_URL}/api/dossier/EST-MDN-001/state")
    assert req_state_mdn.status == 200
    state_mdn_json = json.loads(req_state_mdn.read().decode('utf-8'))
    assert state_mdn_json.get("status") == "success"
    print(f"  ✅ GET /api/dossier/EST-MDN-001/state: dossier_id={state_mdn_json.get('dossier', {}).get('dossier_id')}, telemetry={state_mdn_json.get('telemetry') is not None}, evidence={state_mdn_json.get('latest_evidence') is not None}")

    # -------------------------------------------------------------
    # 4. TEST POST /api/spatial/inspect
    # -------------------------------------------------------------
    print("\n[TEST 4/7] POST /api/spatial/inspect")
    spatial_payload = json.dumps({
        "dossier_id": new_dossier_id,
        "block_id": "BLOK-C01",
        "slope_deg": 14.85,
        "elevation_m": 128.4,
        "canopy_density_pct": 82.5,
        "soil_moisture_pct": 28.3,
        "gps_lat": 0.835412,
        "gps_lng": 101.425102,
        "polygon_geojson": '{"type": "Polygon", "coordinates": [[[101.4, 0.8], [101.5, 0.8], [101.5, 0.9], [101.4, 0.8]]]}'
    }).encode('utf-8')
    req_spatial = urllib.request.Request(f"{BASE_URL}/api/spatial/inspect", data=spatial_payload, headers={'Content-Type': 'application/json'})
    res_spatial = urllib.request.urlopen(req_spatial)
    assert res_spatial.status in [200, 201]
    res_spatial_json = json.loads(res_spatial.read().decode('utf-8'))
    assert res_spatial_json.get("status") == "success"
    print(f"  ✅ POST /api/spatial/inspect berhasil: telemetry_id={res_spatial_json.get('telemetry_id')}, slope={res_spatial_json.get('slope_deg')}°, elev={res_spatial_json.get('elevation_m')}m")

    # -------------------------------------------------------------
    # 5. TEST POST /api/evidence/upload & ANTI-FRAUD
    # -------------------------------------------------------------
    print("\n[TEST 5/7] POST /api/evidence/upload & Anti-Fraud SHA-256")
    fresh_bytes = f"BINARY_JPEG_EVIDENCE_DATA_{time.time()}_{unique_suffix}".encode('utf-8')
    fresh_b64 = base64.b64encode(fresh_bytes).decode('utf-8')
    fresh_sha256 = hashlib.sha256(fresh_bytes).hexdigest()

    evidence_payload = json.dumps({
        "dossier_id": new_dossier_id,
        "block_id": "BLOK-C01",
        "perspective_mode": "CANOPY_DRONE",
        "image_base64": fresh_b64,
        "gps_lat": 0.835412,
        "gps_lng": 101.425102,
        "audit_year": "2026"
    }).encode('utf-8')

    # Initial Upload -> Must succeed
    req_ev_up = urllib.request.Request(f"{BASE_URL}/api/evidence/upload", data=evidence_payload, headers={'Content-Type': 'application/json'})
    res_ev_up = urllib.request.urlopen(req_ev_up)
    assert res_ev_up.status in [200, 201]
    res_ev_json = json.loads(res_ev_up.read().decode('utf-8'))
    evidence_id = res_ev_json.get("evidence_id")
    assert evidence_id, "Evidence ID should be returned"
    print(f"  ✅ Upload foto pertama berhasil: evidence_id={evidence_id}, sha256={fresh_sha256[:16]}...")

    # Duplicate Upload -> Must be rejected with HTTP 409
    try:
        req_dup = urllib.request.Request(f"{BASE_URL}/api/evidence/upload", data=evidence_payload, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req_dup)
        raise AssertionError("❌ Duplicate photo was not blocked with 409!")
    except urllib.error.HTTPError as err:
        assert err.code == 409, f"Expected 409, got {err.code}"
        print(f"  ✅ Anti-fraud SHA-256 terbukti aktif: Foto duplikat ditolak dengan HTTP 409 Conflict")

    # -------------------------------------------------------------
    # 6. TEST GET /api/media/evidence/<evidence_id> (Streaming Biner)
    # -------------------------------------------------------------
    print("\n[TEST 6/7] GET /api/media/evidence/<evidence_id> (Binary Stream)")
    req_stream = urllib.request.urlopen(f"{BASE_URL}/api/media/evidence/{evidence_id}")
    assert req_stream.status == 200
    streamed_data = req_stream.read()
    assert streamed_data == fresh_bytes, "Streamed binary payload mismatch with uploaded bytes"
    print(f"  ✅ GET /api/media/evidence/{evidence_id} berhasil: {len(streamed_data)} bytes streaming biner 100% cocok!")

    # -------------------------------------------------------------
    # 7. TEST POST /api/simulate/run (LER & TBS Pricing Formula)
    # -------------------------------------------------------------
    print("\n[TEST 7/7] POST /api/simulate/run (LER & TBS Pricing Engine)")
    sim_payload = json.dumps({
        "dossier_id": new_dossier_id,
        "companion_crop": "Jahe Merah (Zingiber officinale var. rubrum)",
        "audit_year": 2026
    }).encode('utf-8')

    req_sim = urllib.request.Request(f"{BASE_URL}/api/simulate/run", data=sim_payload, headers={'Content-Type': 'application/json'})
    res_sim = urllib.request.urlopen(req_sim)
    assert res_sim.status in [200, 201]
    res_sim_json = json.loads(res_sim.read().decode('utf-8'))
    assert res_sim_json.get("status") == "success"
    sim_id = res_sim_json.get("simulation_id")
    biophys = res_sim_json.get("biophysics", {})
    ler = biophys.get("ler")
    fin = res_sim_json.get("financial_real", {})
    harga_tbs = fin.get("sawit", {}).get("harga_per_kg_idr")
    total_rev = fin.get("total_gabungan_idr")

    print(f"  ✅ POST /api/simulate/run berhasil:")
    print(f"     - Simulation ID: {sim_id}")
    print(f"     - Land Equivalent Ratio (LER): {ler} (Efisiensi lahan +{(ler - 1.0)*100:.1f}%)")
    print(f"     - Harga TBS Formula Riil: Rp {harga_tbs:,.2f} /kg")
    print(f"     - Total Pendapatan Gabungan Agroforestri: Rp {total_rev:,.0f} /ha/thn")

    print("\n" + "=" * 70)
    print("🏆 SELURUH 7 ENDPOINT TAHAP 2 LOLOS PENGUJIAN 100% TANPA ERROR!")
    print("=" * 70)

if __name__ == '__main__':
    run_all_tahap2_tests()
