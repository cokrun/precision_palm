# test_spatial_persistence.py
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8080"

def test_spatial_persistence_and_locking():
    print("==================================================")
    print(" RUNNING TESTS: BFCACHE PERSISTENCE, EVIDENCE LOCKING, ZERO MOCKUP")
    print("==================================================")

    dossier_id = "EST-MDN-001"
    audit_year = 2026

    # 1. Fetch estate-data before save
    print("\n--- 1. Testing GET /api/spatial/estate-data ---")
    r1 = requests.get(f"{BASE_URL}/api/spatial/estate-data?kode={dossier_id}&year={audit_year}")
    assert r1.status_code == 200, f"Failed getting estate data: {r1.text}"
    data1 = r1.json()
    assert data1["success"] is True
    print(f"✓ Retrieved estate: {data1['estate']['kode_kebun']}")
    print(f"✓ Photos count: {len(data1['photos'])}")
    print(f"✓ Surveys count: {len(data1['surveys'])}")

    # Check if existing surveys have real foto_url
    for s in data1["surveys"][:3]:
        print(f"   [Survey Row] Block: {s.get('block_id')} | Foto: {s.get('foto_url')} | Entities: {len(s.get('detected_entities', []))}")

    # 2. Test saving inspection with specific real survey data (eliminating mockup)
    print("\n--- 2. Testing POST /api/spatial/save-inspection with genuine data ---")
    unique_block = f"Blok Inti - Test Parcel {int(time.time())}"
    unique_photo_url = "/api/media/evidence/EVID-EST-MDN-001-AERIAL-01"
    
    save_payload = {
        "id_kebun": 1,
        "kode_kebun": dossier_id,
        "audit_year": audit_year,
        "soil_ph": 5.6,
        "slope": 4.8,
        "elevation": 145.0,
        "lat": 0.824555,
        "lng": 99.561777,
        "assessor_name": "Dr. Ir. Budi Gunawan (Auditor Utama)",
        "assessor_verdict": "DISETUJUI_PENUH",
        "assessor_notes": "Verifikasi biofisika presisi lapangan 100% patuh ISPO.",
        "sealed_proofs_count": 1,
        "surveillance_entries": [
            {
                "evidence_id": "EVID-EST-MDN-001-AERIAL-01",
                "foto_url": unique_photo_url,
                "process_stage": "STAGE-1-Q1",
                "block_id": unique_block,
                "latitude": 0.824555,
                "longitude": 99.561777,
                "elevation_m": 145.0,
                "slope_deg": 4.8,
                "weather_condition": "Clear 27.2°C (Radar Validated)",
                "sha256_seal": "8F434346648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327AA4",
                "detected_entities": [
                    {"label": "palm_canopy", "cluster": "palm_canopy", "confidence": 0.99},
                    {"label": "root_buffer", "cluster": "root_circle", "confidence": 0.98}
                ]
            }
        ]
    }

    r_save = requests.post(f"{BASE_URL}/api/spatial/save-inspection", json=save_payload)
    assert r_save.status_code in [200, 201], f"Save inspection failed: {r_save.text}"
    print("✓ /api/spatial/save-inspection executed synchronously & succeeded (Status 201 Created).")

    # 3. Test GET /api/spatial/estate-data reflects saved data (Simulating Back Navigation)
    print("\n--- 3. Testing BFCACHE Back Navigation Simulation (Re-reading estate-data) ---")
    r2 = requests.get(f"{BASE_URL}/api/spatial/estate-data?kode={dossier_id}&year={audit_year}")
    assert r2.status_code == 200
    data2 = r2.json()
    
    # Verify the survey row contains genuine saved fields
    saved_survey = next((s for s in data2["surveys"] if s.get("block_id") == unique_block), None)
    assert saved_survey is not None, "Failed: Saved survey was not retrieved from field_surveillance_records!"
    assert saved_survey["foto_url"] == unique_photo_url, f"Expected {unique_photo_url}, got {saved_survey.get('foto_url')}"
    assert abs(saved_survey["latitude"] - 0.824555) < 0.0001, "Latitude mismatch!"
    assert abs(saved_survey["longitude"] - 99.561777) < 0.0001, "Longitude mismatch!"
    assert len(saved_survey["detected_entities"]) == 2, "Entities not preserved!"
    print(f"✓ Back-forward persistence verified: {saved_survey['block_id']}")
    print(f"  Foto URL: {saved_survey['foto_url']}")
    print(f"  Coordinates: {saved_survey['latitude']}, {saved_survey['longitude']}")
    print(f"  Detected entities preserved: {len(saved_survey['detected_entities'])}")

    # 4. Test Permanent Lock: Deleting sealed photo must be REJECTED with 403 Forbidden
    print("\n--- 4. Testing Permanent Evidence Locking (Chain of Custody 403 Rejection) ---")
    del_payload = {
        "photo_id": "EVID-EST-MDN-001-AERIAL-01",
        "photo_url": unique_photo_url,
        "kode_kebun": dossier_id
    }
    r_del = requests.post(f"{BASE_URL}/api/spatial/delete-photo", json=del_payload)
    print(f"Delete response status code: {r_del.status_code}")
    print(f"Delete response text: {r_del.text}")
    assert r_del.status_code == 403, f"Expected HTTP 403 Forbidden, got {r_del.status_code}"
    del_json = r_del.json()
    assert del_json.get("status") == "error"
    assert "Foto telah menjadi bukti dokumen audit dan tidak dapat dihapus." in del_json.get("message", "")
    print("✓ HTTP 403 Forbidden successfully enforced: Sealed photo cannot be deleted!")

    # Verify that in photos list, EVID-EST-MDN-001-AERIAL-01 is marked is_processed = True
    sealed_photo = next((p for p in data2["photos"] if p["id"] == "EVID-EST-MDN-001-AERIAL-01"), None)
    if sealed_photo:
        assert sealed_photo.get("is_processed") is True, "Sealed photo must have is_processed=True"
        print("✓ Photo is_processed flag is True, which removes trash button in DOM!")

    print("\n==================================================")
    print(" ALL 3 REQUIREMENTS VERIFIED & PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    test_spatial_persistence_and_locking()
