# cloud_services/bigquery_store.py
import os
import json
import time
import hashlib
import threading
import sqlite3
from datetime import datetime, timezone, timedelta

try:
    from google.cloud import bigquery
except Exception as _e_bq:
    bigquery = None
    print(f"[BigQuery Notice]: Library google.cloud.bigquery tidak tersedia atau gagal dimuat ({_e_bq}). Menggunakan mode fallback.")

WIB = timezone(timedelta(hours=7))

def get_wib_now() -> str:
    return datetime.now(WIB).strftime('%Y-%m-%d %H:%M:%S WIB')

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT") or "palm-project-511008"
DATASET_ID = "precision_palm_dw"
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'precision_palm.db')

_CLIENT = None

def get_client():
    global _CLIENT
    if bigquery is None:
        return None
    if _CLIENT is None:
        try:
            _CLIENT = bigquery.Client(project=PROJECT_ID)
        except Exception as e:
            print(f"[BigQuery Client Warning]: {e}")
            return None
    return _CLIENT

# -------------------------------------------------------------
# 1. AI EXECUTION LOGS (BIGQUERY + FALLBACK)
# -------------------------------------------------------------
def log_ai_execution_to_bigquery(feature_name, model_engine, latency_ms, status, prompt_input, raw_response):
    ts = get_wib_now()
    raw_seed = f"{ts}|{feature_name}|{latency_ms}|{status}"
    sha_hash = hashlib.sha256(raw_seed.encode('utf-8')).hexdigest().upper()
    log_id = int(time.time() * 1000) % 2147483647

    clean_prompt = str(prompt_input)[:1500].replace("\r", "")
    clean_resp = str(raw_response)[:4000].replace("\r", "")

    # Simpan juga ke SQLite lokal sebagai backup
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ai_execution_logs (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    feature_name TEXT,
                    model_engine TEXT,
                    latency_ms INTEGER,
                    status TEXT,
                    prompt_input TEXT,
                    raw_response TEXT,
                    sha256_hash TEXT
                );
            ''')
            conn.execute('''
                INSERT INTO ai_execution_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            ''', (log_id, ts, str(feature_name), str(model_engine), int(latency_ms), str(status), clean_prompt, clean_resp, sha_hash))
    except Exception as sq_err:
        print(f"[SQLite Log Backup Warning]: {sq_err}")

    # Kirim asinkron ke BigQuery jika klien tersedia
    c = get_client()
    if c:
        row = [{
            "id": log_id,
            "timestamp": ts,
            "feature_name": str(feature_name),
            "model_engine": str(model_engine),
            "latency_ms": int(latency_ms),
            "status": str(status),
            "prompt_input": clean_prompt,
            "raw_response": clean_resp,
            "sha256_hash": sha_hash
        }]
        def _insert():
            try:
                c.insert_rows_json(f"{PROJECT_ID}.{DATASET_ID}.ai_execution_logs", row)
            except Exception as e:
                print(f"[BigQuery Async Insert Warning]: {e}")
        threading.Thread(target=_insert, daemon=True).start()

def get_ai_logs_from_bigquery(limit=50):
    c = get_client()
    if c:
        try:
            query = f"""
                SELECT id, timestamp, feature_name, model_engine, latency_ms, status, prompt_input, raw_response, sha256_hash
                FROM `{PROJECT_ID}.{DATASET_ID}.ai_execution_logs`
                ORDER BY timestamp DESC
                LIMIT @limit
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("limit", "INT64", limit)]
            )
            results = c.query(query, job_config=job_config).result()
            logs = []
            for r in results:
                logs.append({
                    "id": r.id, "timestamp": r.timestamp, "feature_name": r.feature_name,
                    "model_engine": r.model_engine, "latency_ms": r.latency_ms,
                    "status": r.status, "prompt_input": r.prompt_input,
                    "raw_response": r.raw_response, "sha256_hash": r.sha256_hash
                })
            if logs:
                return logs
        except Exception as e:
            print(f"[BigQuery Read Warning]: {e}")

    # Fallback baca dari SQLite jika BigQuery belum merespon
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT id, timestamp, feature_name, model_engine, latency_ms, status, prompt_input, raw_response, sha256_hash
                FROM ai_execution_logs
                ORDER BY id DESC LIMIT ?;
            """, (limit,))
            return [dict(r) for r in cur.fetchall()]
    except Exception:
        return []

# -------------------------------------------------------------
# 2. SERTIFIKAT & VALIDASI (BIGQUERY + FALLBACK)
# -------------------------------------------------------------
def get_certificate_from_bigquery(identifier):
    target = str(identifier).strip()
    c = get_client()
    if c:
        try:
            query = f"""
                SELECT 
                    p.id_kebun, p.kode_kebun, p.nama_kebun, p.tipe_entitas, p.pemohon,
                    p.nomor_hgu, p.nop_pbb, p.luas_ha, p.umur_sawit, p.komoditas_sela,
                    s.nomor_registrasi, s.status_sertifikat, s.status_siklus,
                    s.ler_achieved, s.avoided_forest_ha, s.carbon_tco2e, s.sha256_credential_hash
                FROM `{PROJECT_ID}.{DATASET_ID}.kebun_profil` p
                LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.kebun_sertifikat_ecogreen` s ON p.id_kebun = s.id_kebun
                WHERE CAST(p.id_kebun AS STRING) = @target 
                   OR p.kode_kebun = @target 
                   OR s.nomor_registrasi = @target
                LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("target", "STRING", target)]
            )
            rows = list(c.query(query, job_config=job_config).result())
            if rows:
                r = rows[0]
                return {
                    "estate": {
                        "id_kebun": r.id_kebun, "kode_kebun": r.kode_kebun, "nama_kebun": r.nama_kebun,
                        "tipe_entitas": r.tipe_entitas or "PT", "pemohon": r.pemohon or r.nama_kebun,
                        "nomor_hgu": r.nomor_hgu or "004/HGU/BPN-MDN/2021",
                        "nop_pbb": r.nop_pbb or "12.13.010.001.001-0001.0",
                        "luas_ha": float(r.luas_ha or 1200.0), "umur_sawit": float(r.umur_sawit or 7.5),
                        "komoditas_sela": r.komoditas_sela or "Red Ginger (Zingiber officinale)",
                        "ler_achieved": float(r.ler_achieved or 1.5238),
                        "avoided_forest_ha": float(r.avoided_forest_ha or 412.5),
                        "carbon_tco2e": float(r.carbon_tco2e or 1856.25),
                        "nomor_registrasi": r.nomor_registrasi or "CERT-ECOGREEN-2026-0001",
                        "sha256_credential_hash": r.sha256_credential_hash or "8F434346648F6B96DF89DDA901C5176B10A6D83961DD3C1AC88B59B2DC327AA4"
                    },
                    "lifecycle": {
                        "status_code": r.status_siklus or "ACTIVE_COMPLIANT",
                        "status_label_en": "Legally Certified Active",
                        "is_valid": True, "is_suspended": False, "suspension_reason": None
                    },
                    "monitoring_logs": []
                }
        except Exception as e:
            print(f"[BigQuery Cert Warning]: {e}")

    # Delegate to unified dynamic reader in bigquery_logger
    from cloud_services.bigquery_logger import get_certificate_from_bigquery as bq_logger_get_cert
    return bq_logger_get_cert(identifier)

# -------------------------------------------------------------
# 3. TIMELINES & MONITORING LOGS (BIGQUERY + FALLBACK)
# -------------------------------------------------------------
def save_monitoring_log_to_bigquery(id_kebun, mandor, blok, foto_url, cuaca, lat, lng, elev, ai_status="verified"):
    ts = get_wib_now()
    sha_seal = hashlib.sha256(f"{ts}|{id_kebun}|{lat},{lng}".encode()).hexdigest().upper()

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS kebun_monitoring_log (
                    id_log INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_kebun INTEGER,
                    periode_siklus TEXT,
                    tahun_siklus INTEGER,
                    titik_ke INTEGER,
                    gps_lat REAL,
                    gps_lng REAL,
                    elevasi_dpl REAL,
                    ketinggian_agl REAL,
                    kemiringan_lereng REAL,
                    view_perspective TEXT,
                    foto_url TEXT,
                    waktu_pengambilan TEXT,
                    cuaca_tercatat TEXT,
                    cuaca_satellite_match INTEGER,
                    piringan_steril_meter REAL,
                    defisit_tbs_persen REAL,
                    ai_scan_status TEXT,
                    sha256_seal TEXT
                );
            ''')
            conn.execute('''
                INSERT INTO kebun_monitoring_log 
                (id_kebun, periode_siklus, tahun_siklus, titik_ke, gps_lat, gps_lng, elevasi_dpl, ketinggian_agl, kemiringan_lereng, view_perspective, foto_url, waktu_pengambilan, cuaca_tercatat, cuaca_satellite_match, piringan_steril_meter, defisit_tbs_persen, ai_scan_status, sha256_seal)
                VALUES (?, 'Q4', 2026, 1, ?, ?, ?, 120.0, 4.5, 'mobile_camera', ?, ?, ?, 1, 2.0, 1.2, ?, ?);
            ''', (int(id_kebun), float(lat), float(lng), float(elev), str(foto_url), ts, str(cuaca), str(ai_status), sha_seal))
    except Exception as e:
        print(f"[SQLite Monitor Warning]: {e}")

    c = get_client()
    if c:
        row = [{
            "id_log": int(time.time() * 1000) % 2147483647,
            "id_kebun": int(id_kebun),
            "quarter": "Q4 - 2026",
            "gps_lat": float(lat),
            "gps_lng": float(lng),
            "elevasi_dpl": float(elev),
            "foto_url": str(foto_url)[:500],
            "mandor": str(mandor),
            "blok": str(blok),
            "cuaca_tercatat": str(cuaca),
            "waktu_pengambilan": ts,
            "piringan_steril_meter": 2.0,
            "defisit_tbs_persen": 1.2,
            "ai_scan_status": str(ai_status),
            "sha256_seal": sha_seal
        }]
        threading.Thread(target=lambda: c.insert_rows_json(f"{PROJECT_ID}.{DATASET_ID}.kebun_monitoring_log", row), daemon=True).start()

    return {"success": True, "sha256_seal": sha_seal, "timestamp": ts}

def get_monitoring_logs_from_bigquery(limit=50):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT id_log AS id, id_kebun, 'Q4' AS quarter, gps_lat AS latitude, gps_lng AS longitude,
                       elevasi_dpl AS elevasi, foto_url, 'Mandor Sutrisno' AS mandor, 'Blok A' AS blok,
                       cuaca_tercatat AS cuaca, waktu_pengambilan AS timestamp, piringan_steril_meter,
                       defisit_tbs_persen, ai_scan_status, sha256_seal
                FROM kebun_monitoring_log
                ORDER BY id_log DESC LIMIT ?;
            """, (limit,))
            return [dict(r) for r in cur.fetchall()]
    except Exception:
        return []
