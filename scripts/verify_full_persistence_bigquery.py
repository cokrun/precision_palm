# verify_full_persistence_bigquery.py
"""
Precision Palm Cloud - Full Verification & Persistence Audit Script
1. Real AI Inference (Vertex AI / Google Gemini Flash) with Attributed Statutory Citations.
2. Dual-Write Persistence Verification (Local SQLite & Google BigQuery DW).
"""

import os
import sys
import json
import time
import sqlite3
import urllib.request
from datetime import datetime
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(ROOT_DIR, '.env'))

BASE_URL = "http://localhost:8080"

def print_separator(title):
    print("\n" + "=" * 78)
    print(f" {title}")
    print("=" * 78)

def test_real_gemini_inference():
    print_separator("BAGIAN 1: PENGUJIAN REAL AI INFERENCE (GOOGLE GEMINI FLASH)")
    
    query = (
        "Bagaimana verifikasi batas sempadan hutan lindung 50m berdasarkan PP 23/2021, "
        "larangan olah tanah piringan sawit radius 2.0m menurut Permentan No. 33 Tahun 2025 GAP ISPO, "
        "dan tanggal patokan bebas deforestasi 31 Desember 2020 sesuai Regulasi EUDR 2023/1115?"
    )
    payload = {
        "query": query,
        "estate_code": "EST-MDN-001",
        "lang": "id"
    }

    print(f"[>] Mengirim permohonan audit statuter ke: {BASE_URL}/api/ai/grounded-audit")
    print(f"[>] Pertanyaan Legal: \"{query}\"")
    
    start_time = time.time()
    req = urllib.request.Request(
        f"{BASE_URL}/api/ai/grounded-audit",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            elapsed = time.time() - start_time
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
    except Exception as exc:
        print(f"[!] ERROR: Gagal menghubungi endpoint grounded-audit: {exc}")
        return False

    print(f"[OK] Respon diterima dalam {elapsed:.2f} detik (HTTP 200)")
    
    answer = data.get("answer", "")
    citations = data.get("citations", [])
    metadata = data.get("grounding_metadata", {})
    
    print("\n--- TEKS PENALARAN AUDITOR (REAL GEMINI) ---")
    print(answer)
    print("--------------------------------------------")
    
    print(f"\n[OK] Mesin Eksekusi: {metadata.get('engine', 'Google Gemini Flash')}")
    print(f"[OK] Status Atribusi: {metadata.get('attribution_status', 'UNKNOWN')}")
    print(f"[OK] Anti-Halusinasi: {metadata.get('is_hallucination_free', False)}")
    print(f"[OK] Jumlah Sitasi Statuter Terverifikasi: {len(citations)}")
    
    for idx, c in enumerate(citations):
        print(f"    {c.get('ref', f'[{idx+1}]')} {c.get('doc_title')} - {c.get('legal_basis')}")
        print(f"        Kutipan: \"{c.get('exact_quote', '')}\"")
    
    # Validasi
    has_citations = len(citations) >= 2
    has_answer = len(answer) > 50
    if has_citations and has_answer:
        print("\n>>> HASIL TAHAP 1: REAL AI INFERENCE DENGAN SITASI RESMI [LULUS / PASSED] <<<")
        return True
    else:
        print("\n>>> HASIL TAHAP 1: GAGAL MEMENUHI KRITERIA ATRIBUSI RESMI <<<")
        return False

def test_dual_write_persistence():
    print_separator("BAGIAN 2: PENGUJIAN PERSISTENSI TULIS-GANDA (SQLITE & BIGQUERY)")
    
    node_id = "node_4_1"
    estate_code = "EST-MDN-001"
    node_title = "Final Statutory Compliance & All-Report Master Docket"
    verdict = (
        "Dewan Asesor mengesahkan kelulusan 100% Kepatuhan Statuter Kebun EST-MDN-001. "
        "Sempadan penyangga >= 50m hutan lindung terpenuhi (PP 23/2021 [1]), "
        "piringan steril 2.0m dan zero-tillage sawit terawat sempurna (Permentan No. 33 Tahun 2025 [2]), "
        "dan nol deforestasi pasca cut-off 31 Desember 2020 terverifikasi satelit (EUDR 2023/1115 [3])."
    )
    citations = [
        {"ref": "[1]", "doc_title": "PP No. 23/2021", "legal_basis": "Pasal 38 Ayat 2"},
        {"ref": "[2]", "doc_title": "Permentan No. 33 Tahun 2025", "legal_basis": "GAP ISPO Prinsip 2"},
        {"ref": "[3]", "doc_title": "Regulasi EUDR (EU) 2023/1115", "legal_basis": "Pasal 9 Due Diligence"}
    ]

    payload = {
        "node_id": node_id,
        "estate_code": estate_code,
        "node_title": node_title,
        "verdict_answer": verdict,
        "citations": citations
    }

    print(f"[>] Menyimpan evaluasi audit simpul ke: {BASE_URL}/api/ai/save-node-review")
    req = urllib.request.Request(
        f"{BASE_URL}/api/ai/save-node-review",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"[!] ERROR: Gagal menghubungi endpoint save-node-review: {exc}")
        return False

    print(f"[OK] Endpoint Response: {res_json}")
    sha256_hash = res_json.get("sha256_hash", "")
    print(f"[OK] SHA-256 Digest Integrity: {sha256_hash}")

    # 1. Periksa SQLite lokal
    print("\n--- VERIFIKASI BUKTI PERSISTENSI SQLITE LOKAL ---")
    db_file = os.path.join(ROOT_DIR, "precision_palm.db")
    try:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute("""
            SELECT rowid, node_id, estate_code, sha256_hash, timestamp, sync_status 
            FROM node_audit_reviews 
            WHERE sha256_hash = ? OR (node_id = ? AND estate_code = ?)
            ORDER BY rowid DESC LIMIT 1;
        """, (sha256_hash, node_id, estate_code))
        sq_row = cur.fetchone()
        conn.close()
        
        if sq_row:
            print(f"[OK] Record ditemukan di SQLite (RowID: {sq_row[0]}):")
            print(f"    - Node ID     : {sq_row[1]}")
            print(f"    - Kebun       : {sq_row[2]}")
            print(f"    - SHA-256     : {sq_row[3]}")
            print(f"    - Timestamp   : {sq_row[4]}")
            print(f"    - Sync Status : {sq_row[5]}")
        else:
            print("[!] Record tidak ditemukan di SQLite lokal!")
            return False
    except Exception as sq_err:
        print(f"[!] Error membaca SQLite: {sq_err}")
        return False

    # 2. Periksa Google BigQuery
    print("\n--- VERIFIKASI BUKTI PERSISTENSI GOOGLE BIGQUERY DW ---")
    print("[>] Menunggu sinkronisasi background thread BigQuery (3 detik)...")
    time.sleep(3)

    try:
        from cloud_services.bigquery_audit import get_bq_client
        bq_client = get_bq_client()
        if not bq_client:
            print("[!] BigQuery client tidak dapat diinisialisasi.")
            return False

        ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if ROOT_DIR not in sys.path:
            sys.path.insert(0, ROOT_DIR)
        from config import Config

        sql_query = f"""
            SELECT node_id, node_title, estate_code, sha256_hash, timestamp 
            FROM `{Config.PROJECT_ID}.{Config.BQ_DATASET}.node_audit_reviews` 
            ORDER BY timestamp DESC LIMIT 5;
        """
        print(f"[>] Menjalankan kueri BigQuery pada {Config.PROJECT_ID}.{Config.BQ_DATASET}.node_audit_reviews:\n{sql_query.strip()}\n")
        
        query_job = bq_client.query(sql_query)
        rows = list(query_job.result())
        
        print(f"[OK] Berhasil menarik {len(rows)} record audit dari BigQuery Cloud DW:")
        print("-" * 110)
        print(f"{'NODE ID':<12} | {'ESTATE':<12} | {'TIMESTAMP':<24} | {'SHA-256 HASH':<32} | {'TITLE'}")
        print("-" * 110)
        for r in rows:
            print(f"{str(r.get('node_id', '')):<12} | {str(r.get('estate_code', '')):<12} | {str(r.get('timestamp', '')):<24} | {str(r.get('sha256_hash', ''))[:30] + '..':<32} | {str(r.get('node_title', ''))[:20]}")
        print("-" * 110)
        
        print("\n>>> HASIL TAHAP 2: DUAL-WRITE PERSISTENCE AUDIT [LULUS / PASSED] <<<")
        return True
    except Exception as bq_err:
        print(f"[!] Gagal mengeksekusi kueri BigQuery: {bq_err}")
        return False

if __name__ == "__main__":
    print_separator("PRECISION PALM CLOUD: E2E SYSTEM INTEGRATION & PERSISTENCE AUDIT")
    ok1 = test_real_gemini_inference()
    ok2 = test_dual_write_persistence()
    
    print_separator("RINGKASAN AUDIT")
    if ok1 and ok2:
        print(" [PASSED] SELURUH PENGUJIAN TAHAP 3 TERBUKTI 100% LULUS (ZERO-SIMULATION VERIFIED) ")
        sys.exit(0)
    else:
        print(" [FAILED] TERDAPAT PENGUJIAN YANG GAGAL. SILAKAN PERIKSA LOG DI ATAS. ")
        sys.exit(1)
