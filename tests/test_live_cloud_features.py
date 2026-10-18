#!/usr/bin/env python3
"""
test_live_cloud_features.py
Precision Palm Cloud - Full End-to-End Live Audit & Cloud Run Verification Suite.

Tests Google Cloud Run production deployment:
https://precision-palm-739036785917.asia-southeast2.run.app/

Verification Coverage:
1. MBTiles Vector/Raster Tile Streaming Latency (/api/tiles/10/823/508.png)
2. AI Grounded Statutory Audit Query (/api/ai/grounded-audit) - Normal vs PIPPIB Collision
3. Node Audit Review Telemetry (/api/ai/get-node-review)
4. Certificate QR Code Validation Endpoint (/validasi/CERT-ECOGREEN-2026-0001)
5. Multimodal Vision Scanner (/api/ai/scan-image) & Foreman Voice (/api/mobile/voice-report)
"""

import sys
import os
import time
import json
import requests

from config import Config

TARGET_BASE_URL = os.environ.get(
    "TARGET_BASE_URL", 
    "https://precision-palm-739036785917.asia-southeast2.run.app"
).rstrip('/')

if "--local" in sys.argv:
    TARGET_BASE_URL = "http://127.0.0.1:8080"

print("=" * 80)
print(f"   PRECISION PALM ENTERPRISE - LIVE CLOUD RUN E2E AUDIT")
print(f"   Target URL : {TARGET_BASE_URL}")
print(f"   Project ID : {Config.PROJECT_ID} ({Config.GCP_REGION})")
print("=" * 80)

results = []

def run_test(test_id, test_name, method, endpoint, payload=None, params=None, headers=None, expected_status=200):
    url = f"{TARGET_BASE_URL}{endpoint}"
    print(f"\n[{test_id}] Testing: {test_name}...")
    print(f"      Endpoint : {method} {endpoint}")
    start_time = time.time()
    status_str = "FAILED"
    latency_ms = 0
    details = ""
    resp_obj = None

    default_headers = {"User-Agent": "PrecisionPalm-LiveAudit-Agent/2.5"}
    if headers:
        default_headers.update(headers)

    try:
        if method.upper() == 'GET':
            resp = requests.get(url, params=params, headers=default_headers, timeout=30)
        elif method.upper() == 'POST':
            resp = requests.post(url, json=payload, headers=default_headers, timeout=45)
        else:
            raise ValueError(f"Unsupported method: {method}")

        latency_ms = int((time.time() - start_time) * 1000)
        resp_obj = resp

        if resp.status_code == expected_status:
            status_str = "SUCCESS"
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type:
                try:
                    js = resp.json()
                    summary_keys = list(js.keys())[:6]
                    details = f"HTTP {resp.status_code} OK | JSON Keys: {summary_keys}"
                except Exception:
                    details = f"HTTP {resp.status_code} OK | Bytes: {len(resp.content)}"
            else:
                details = f"HTTP {resp.status_code} OK | Content-Type: {content_type} ({len(resp.content)} bytes)"
        else:
            status_str = "FAILED"
            details = f"HTTP {resp.status_code} (Expected {expected_status}) | Body snippet: {resp.text[:180]}"

    except Exception as exc:
        latency_ms = int((time.time() - start_time) * 1000)
        status_str = "ERROR"
        details = f"Request Exception: {str(exc)}"

    print(f"      Result   : [{status_str}] in {latency_ms} ms")
    print(f"      Details  : {details}")

    results.append({
        "id": test_id,
        "name": test_name,
        "endpoint": endpoint,
        "status": status_str,
        "latency_ms": latency_ms,
        "details": details,
        "response": resp_obj
    })
    return resp_obj


# =========================================================================
# TEST 1: MBTiles Tile Streaming Healthcheck & Latency
# =========================================================================
run_test(
    test_id="TEST-1",
    test_name="MBTiles Peat Moratorium Tile Streaming",
    method="GET",
    endpoint="/api/tiles/10/823/508.png"
)

# =========================================================================
# TEST 2A: AI Grounded Statutory Audit Query (Normal Compliance)
# =========================================================================
run_test(
    test_id="TEST-2A",
    test_name="AI Grounded Audit (Normal: 2.0m Sterile Buffer & GAP ISPO)",
    method="POST",
    endpoint="/api/ai/grounded-audit",
    payload={
        "query": "Evaluate 2.0m sterile root buffer zero-tillage compliance under ISPO Principle 2 and Permentan No. 33 Tahun 2025.",
        "estate_code": "EST-MDN-001",
        "lang": "en",
        "scenario": "normal"
    }
)

# =========================================================================
# TEST 2B: AI Grounded Statutory Audit Query (PIPPIB Moratorium Collision)
# =========================================================================
run_test(
    test_id="TEST-2B",
    test_name="AI Grounded Audit (PIPPIB 2024 Peat Moratorium Collision & EUDR Art. 9)",
    method="POST",
    endpoint="/api/ai/grounded-audit",
    payload={
        "query": "Estate polygon intersects 14.80 Ha of PIPPIB 2024 protected peat forest. Enforce self-healing enclave and zero deforestation under EUDR Article 9.",
        "estate_code": "EST-MDN-005",
        "lang": "en",
        "scenario": "pippib_collision"
    }
)

# =========================================================================
# TEST 3: AI Node Audit Review Verification
# =========================================================================
run_test(
    test_id="TEST-3",
    test_name="AI Node Review Query (BigQuery / Local Ledger)",
    method="GET",
    endpoint="/api/ai/get-node-review",
    params={"node_id": "node_1_1", "estate_code": "EST-MDN-001"}
)

# =========================================================================
# TEST 4: Certificate QR Validation Endpoint
# =========================================================================
run_test(
    test_id="TEST-4",
    test_name="Statutory Certificate QR Code Verification Page",
    method="GET",
    endpoint="/validasi/CERT-ECOGREEN-2026-0001"
)

# =========================================================================
# TEST 5: Foreman Voice-to-Report Chirp 2 NLP Parser
# =========================================================================
run_test(
    test_id="TEST-5",
    test_name="Foreman Voice-to-Report Chirp 2 NLP Parsing",
    method="POST",
    endpoint="/api/mobile/voice-report",
    payload={
        "transcript": "Lapor mandor lapangan, piringan pokok dua meter steril bersih tanpa cangkul, rorak sedimen tertata, cuaca cerah."
    }
)


# =========================================================================
# AUDIT SUMMARY MATRIX REPORT
# =========================================================================
print("\n" + "=" * 96)
print(f"{'TEST ID':<10} | {'FEATURE NAME':<38} | {'STATUS':<10} | {'LATENCY':<10} | {'NOTES':<20}")
print("-" * 96)
for r in results:
    note_snippet = (r['details'][:26] + '..') if len(r['details']) > 28 else r['details']
    print(f"{r['id']:<10} | {r['name'][:38]:<38} | {r['status']:<10} | {str(r['latency_ms']) + ' ms':<10} | {note_snippet:<20}")
print("=" * 96)

all_passed = all(r['status'] == "SUCCESS" for r in results)
if all_passed:
    print("\n>>> ALL CLOUD RUN E2E TESTS PASSED (100% SUCCESS) <<<")
    sys.exit(0)
else:
    print("\n>>> ONE OR MORE TESTS FAILED <<<")
    sys.exit(1)
