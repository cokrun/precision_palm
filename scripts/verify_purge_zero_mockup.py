import urllib.request
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8080"

def test_url(endpoint):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, headers={'User-Agent': 'MockupPurgeVerifier/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            return resp.status, content
    except Exception as e:
        return 0, str(e)

def run_tests():
    print("=" * 70)
    print("   PRECISION PALM ENTERPRISE: ZERO-MOCKUP PURGE VERIFICATION")
    print("=" * 70)

    # 1. Test EST-RIAU-002 evidence gallery (Must be empty)
    status, body = test_url("/api/dossier/EST-RIAU-002/evidence-gallery")
    data = json.loads(body)
    assert status == 200, f"Gallery returned status {status}"
    assert data.get("count") == 0, f"Expected 0 photos for EST-RIAU-002, got {data.get('count')}"
    print("[✓ PASS] /api/dossier/EST-RIAU-002/evidence-gallery -> 0 photos (Empty State Jujur)")

    # 2. Test EST-RIAU-002 quarterly status (All Q1-Q4 must be PENDING)
    status, body = test_url("/api/estate/quarterly-status?kode=EST-RIAU-002")
    data = json.loads(body)
    assert status == 200, f"Quarterly status returned {status}"
    quarters = data.get("quarters", {})
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        q_stat = quarters.get(q, {}).get("status")
        assert q_stat == "PENDING", f"Expected {q} to be PENDING for EST-RIAU-002, got {q_stat}"
    print("[✓ PASS] /api/estate/quarterly-status?kode=EST-RIAU-002 -> Q1-Q4 PENDING (Nihil Fake Q1)")

    # 3. Test EST-RIAU-002 dossier state
    status, body = test_url("/api/dossier/EST-RIAU-002/state")
    data = json.loads(body)
    assert status == 200, f"Dossier state returned {status}"
    assert data.get("latest_evidence") is None, "Expected latest_evidence=None for EST-RIAU-002"
    assert data.get("telemetry") is None, "Expected telemetry=None for EST-RIAU-002"
    print("[✓ PASS] /api/dossier/EST-RIAU-002/state -> latest_evidence=None (Honest Empty State)")

    # 4. Test HTML pages for absence of leaked sawit_drone.jpg and fake HGU in EST-RIAU-002 context
    pages = [
        ("/concession-register?kode=EST-RIAU-002", "Pendaftaran"),
        ("/planetary-observatory?kode=EST-RIAU-002", "Spatial"),
        ("/in-silico?kode=EST-RIAU-002", "Simulator"),
        ("/quarterly-surveillance?kode=EST-RIAU-002", "Timelines"),
        ("/statutory-ratification?kode=EST-RIAU-002", "Roadmap"),
        ("/compliance-lineage?kode=EST-RIAU-002", "Topologi")
    ]

    for endpoint, name in pages:
        status, html = test_url(endpoint)
        assert status == 200, f"{name} page returned status {status}"
        
        # Check that sawit_drone.jpg is not forced in hidden inputs
        assert '<input type="hidden" id="image_sample" value="sawit_drone.jpg">' not in html, f"Leak: sawit_drone in {name}"
        # Check that fake HGU is not injected in value
        assert 'value="004/HGU/BPN-MDN/2021"' not in html, f"Leak: fake HGU value in {name}"
        # Check that CANONICAL_ESTATES_ZONING is not present
        assert 'CANONICAL_ESTATES_ZONING' not in html, f"Leak: CANONICAL_ESTATES_ZONING in {name}"
        # Check that CANONICAL_ESTATES_SEED is not present
        assert 'CANONICAL_ESTATES_SEED' not in html, f"Leak: CANONICAL_ESTATES_SEED in {name}"
        # Check that DEFAULT_ESTATE_TELEMETRY_SEEDS with fake IDs is not present
        assert 'id: 48196' not in html, f"Leak: fake seed 48196 in {name}"
        
        print(f"[✓ PASS] {name} ({endpoint}) -> Bersih total dari mockup & kebocoran MDN-001")

    # 5. Verify EST-MDN-001 maintains its real evidence
    status, body = test_url("/api/dossier/EST-MDN-001/evidence-gallery")
    data = json.loads(body)
    assert status == 200
    assert data.get("count", 0) >= 2, f"Expected >=2 photos for EST-MDN-001, got {data.get('count')}"
    print(f"[✓ PASS] EST-MDN-001 tetap memiliki {data.get('count')} bukti citra riil database (Non-Regresif)")

    print("=" * 70)
    print("   ALL 5 STAGES OF AUDIT DIRECTIVE SUCCESSFULLY VERIFIED!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
