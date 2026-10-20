#!/usr/bin/env python3
"""
verify_deployed_cloud_run.py
End-to-End Automated Verification for Deployed Google Cloud Run Service: precision-palm
URL: https://precision-palm-boy37shzfa-et.a.run.app
"""

import sys
import os
import time
import json
import base64
import requests

if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

TARGET_URL = os.environ.get("CLOUD_RUN_URL", "https://precision-palm-boy37shzfa-et.a.run.app").rstrip('/')

print("=" * 80)
print("  PRECISION PALM CLOUD RUN: LIVE POST-DEPLOYMENT VERIFICATION")
print(f"  Target URL: {TARGET_URL}")
print("=" * 80 + "\n")

results = []

def run_check(test_id, name, method, path, payload=None, params=None, expected_status=200):
    url = f"{TARGET_URL}{path}"
    headers = {"User-Agent": "PrecisionPalm-LiveAudit/2.5"}
    t0 = time.time()
    status = "FAILED"
    notes = ""
    resp_data = None
    
    try:
        if method.upper() == 'GET':
            resp = requests.get(url, params=params, headers=headers, timeout=30)
        else:
            resp = requests.post(url, json=payload, headers=headers, timeout=45)
        
        latency = int((time.time() - t0) * 1000)
        
        if resp.status_code == expected_status:
            status = "PASSED"
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type:
                resp_data = resp.json()
                notes = f"HTTP {resp.status_code} OK | JSON keys: {len(resp_data)}"
            else:
                notes = f"HTTP {resp.status_code} OK | Content-Type: {content_type[:25]} | Size: {len(resp.content)} bytes"
        else:
            notes = f"HTTP {resp.status_code} (Expected {expected_status}) | Body: {resp.text[:120]}"
    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        notes = f"Error: {str(e)[:120]}"

    icon = "✅ PASS" if status == "PASSED" else "❌ FAIL"
    print(f"[{icon}] [{test_id}] {name:48} | {latency:4d}ms | {notes}")
    
    res = {
        "id": test_id,
        "name": name,
        "method": method,
        "path": path,
        "status": status,
        "latency_ms": latency,
        "notes": notes,
        "data": resp_data
    }
    results.append(res)
    return res

# 1. Root & Health Check
run_check("TEST-01", "Planetary Observatory Dashboard (Root UI)", "GET", "/")

# 2. Config & Governance Endpoint (Zero Secrets)
cfg_res = run_check("TEST-02", "Config Endpoint Zero-Secret Check", "GET", "/api/config")
if cfg_res["data"]:
    cfg = cfg_res["data"].get("config") or cfg_res["data"]
    has_secret = any("API_KEY" in k.upper() or "SECRET" in k.upper() for k in cfg.keys())
    assert not has_secret, "LEAK DETECTED: Secret found in /api/config!"
    print("      -> Governance Verified: Zero Secrets in /api/config")

# 3. Canonical Enterprise Page Redirects & Routes
run_check("TEST-03", "Planetary Observatory Page (/planetary-observatory)", "GET", "/planetary-observatory")
run_check("TEST-04", "In-Silico Agroforestry Lab (/in-silico)", "GET", "/in-silico")
run_check("TEST-05", "Decentralized Registry Timeline (/timelines)", "GET", "/timelines")
run_check("TEST-06", "System Configuration Governance (/pengaturan)", "GET", "/pengaturan")
run_check("TEST-07", "Audit Events Telemetry Log (/ai-logs)", "GET", "/ai-logs")

# 4. Pricing Calculation Engine (TBS Permentan 01/2018)
pricing_payload = {
    "harga_cpo": 14250.0,
    "harga_kernel": 8900.0,
    "indeks_k": 91.25,
    "rendemen_cpo": 21.8,
    "rendemen_kernel": 5.4,
    "biaya_olah": 285.0
}
run_check("TEST-08", "TBS Permentan Pricing Formula", "POST", "/api/pricing/tbs-calculation", pricing_payload)

# 5. Spatial Evidence Analysis (EUDR Art. 9 & ISPO Compliance)
spatial_payload = {
    "dossier_id": "EST-MDN-010",
    "lat": 0.824102,
    "lng": 99.561214,
    "polygon": [[0.8241, 99.5612], [0.8245, 99.5620], [0.8240, 99.5625]]
}
run_check("TEST-09", "Spatial Evidence Analysis (EUDR & ISPO)", "POST", "/api/spatial/evidence-analysis", spatial_payload)

# 6. Foreman Voice Audio / Text Report
voice_payload = {
    "transcript": "Blok C-12 terdeteksi serangan ulat api seluas 4 hektar pada kelapa sawit usia 8 tahun",
    "dossier_id": "EST-MDN-010"
}
run_check("TEST-10", "Foreman Voice NLP Report Processing", "POST", "/api/mobile/voice-report", voice_payload)

# 7. AI Multimodal Vision Scan & Fallback Engine
# Minimal 1x1 transparent PNG base64
dummy_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
scan_payload = {
    "image_b64": dummy_png,
    "block_id": "BLK-C12",
    "feature_name": "Post-Deploy Cloud Run Probe",
    "declared_crop": "Kelapa Sawit",
    "latitude": 0.824102,
    "longitude": 99.561214
}
run_check("TEST-11", "AI Multimodal Vision / Autonomous Rule Engine", "POST", "/api/ai/scan-image", scan_payload)

# 8. Certificate Validation Endpoint
run_check("TEST-12", "Statutory QR Certificate Validation", "GET", "/validasi/CERT-ECOGREEN-2026-0001")

# 9. Spatial MBTiles Raster/Vector Tile Streaming
run_check("TEST-13", "Spatial MBTiles Tile Streaming (/api/tiles/...)", "GET", "/api/tiles/10/823/508.png")

# 10. Relational Audit Export
run_check("TEST-14", "Audit Logs Relational Data Export (/api/database/export/json)", "GET", "/api/database/export/json")

print("\n" + "=" * 80)
total = len(results)
passed = sum(1 for r in results if r["status"] == "PASSED")
failed = total - passed
pass_rate = (passed / total) * 100
avg_latency = sum(r["latency_ms"] for r in results) / total

print(f"  DEPLOYMENT VERIFICATION SUMMARY: {passed}/{total} Passed ({pass_rate:.1f}%) | Avg Latency: {avg_latency:.1f}ms")
print("=" * 80 + "\n")

out_file = os.path.join(os.path.dirname(__file__), "..", "scratch", "cloud_run_verification_results.json")
os.makedirs(os.path.dirname(out_file), exist_ok=True)
with open(out_file, "w", encoding="utf-8") as f:
    json.dump({
        "target_url": TARGET_URL,
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
        "avg_latency_ms": avg_latency,
        "results": results
    }, f, indent=2)
print(f"Results saved to: {out_file}")

if failed > 0:
    sys.exit(1)
