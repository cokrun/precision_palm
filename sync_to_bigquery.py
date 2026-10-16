#!/usr/bin/env python3
"""
sync_to_bigquery.py - Precision Palm Local to BigQuery Ledger Synchronizer
Author: AG Precision Palm Engineering Team
Target Project: palm-project-511008
Target Dataset: precision_palm_ledger
"""

import os
import sys
import sqlite3
import datetime

# Standardize Windows console output encoding to UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
except Exception:
    pass

# Konfigurasi Cloud & Database
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT_ID") or "palm-project-511008"
DATASET_ID = os.environ.get("BIGQUERY_DATASET", "precision_palm_dw")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "precision_palm.db")

def safe_float(val, default=0.0):
    try:
        return float(val) if val is not None and str(val).strip() != '' else default
    except Exception:
        return default

def safe_int(val, default=0):
    try:
        return int(val) if val is not None and str(val).strip() != '' else default
    except Exception:
        return default

def safe_str(val, default=""):
    return str(val).strip() if val is not None else default

def get_bq_client():
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=PROJECT_ID)
        return client
    except Exception as e:
        print(f"[!] Gagal inisialisasi BigQuery Client: {e}")
        print("    Pastikan kredensial Google Cloud aktif (gcloud auth application-default login)")
        return None

def ensure_dataset(client):
    from google.cloud import bigquery
    dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
    try:
        client.get_dataset(dataset_ref)
        print(f"[✓] Dataset BigQuery `{PROJECT_ID}.{DATASET_ID}` sudah tersedia.")
        return True
    except Exception:
        print(f"[*] Dataset `{PROJECT_ID}.{DATASET_ID}` belum ditemukan. Membuat dataset baru...")
        dataset = bigquery.Dataset(dataset_ref)
        try:
            dataset.location = "asia-southeast2"
            client.create_dataset(dataset, timeout=30)
            print(f"[✓] Berhasil membuat dataset `{PROJECT_ID}.{DATASET_ID}` (Region: asia-southeast2).")
            return True
        except Exception as e_loc:
            try:
                dataset.location = None
                client.create_dataset(dataset, timeout=30)
                print(f"[✓] Berhasil membuat dataset `{PROJECT_ID}.{DATASET_ID}`.")
                return True
            except Exception as e_create:
                print(f"[!] Gagal membuat dataset BigQuery: {e_create}")
                return False

def sync_estates(client, conn):
    from google.cloud import bigquery
    table_id = f"{PROJECT_ID}.{DATASET_ID}.estates"
    schema = [
        bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("id_kebun", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("kode_kebun", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("nama_kebun", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("tipe_entitas", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("pemohon", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("kontak", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("nomor_hgu", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("nop_pbb", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("luas_ha", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("umur_sawit", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("komoditas_sela", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("centroid_lat", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("centroid_lng", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("status_sertifikat", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("nomor_registrasi", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("doc_legal_url", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("created_at", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("synced_at", "STRING", mode="NULLABLE")
    ]

    try:
        client.get_table(table_id)
    except Exception:
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)
        print(f"[✓] Tabel BigQuery `{table_id}` berhasil dibuat.")

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM estates;")
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]

    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    payload = []
    for r in rows:
        row_dict = dict(zip(cols, r))
        payload.append({
            "id": safe_int(row_dict.get("id")),
            "id_kebun": safe_int(row_dict.get("id_kebun")),
            "kode_kebun": safe_str(row_dict.get("kode_kebun")),
            "nama_kebun": safe_str(row_dict.get("nama_kebun")),
            "tipe_entitas": safe_str(row_dict.get("tipe_entitas"), "PT"),
            "pemohon": safe_str(row_dict.get("pemohon")),
            "kontak": safe_str(row_dict.get("kontak")),
            "nomor_hgu": safe_str(row_dict.get("nomor_hgu")),
            "nop_pbb": safe_str(row_dict.get("nop_pbb")),
            "luas_ha": safe_float(row_dict.get("luas_ha")),
            "umur_sawit": safe_float(row_dict.get("umur_sawit")),
            "komoditas_sela": safe_str(row_dict.get("komoditas_sela")),
            "centroid_lat": safe_float(row_dict.get("centroid_lat")),
            "centroid_lng": safe_float(row_dict.get("centroid_lng")),
            "status_sertifikat": safe_str(row_dict.get("status_sertifikat")),
            "nomor_registrasi": safe_str(row_dict.get("nomor_registrasi")),
            "doc_legal_url": safe_str(row_dict.get("doc_legal_url")),
            "created_at": safe_str(row_dict.get("created_at")),
            "synced_at": now_str
        })

    if payload:
        delete_job = client.query(f"DELETE FROM `{table_id}` WHERE true")
        delete_job.result()
        errors = client.insert_rows_json(table_id, payload)
        if not errors:
            print(f"[✓] SUKSES: {len(payload)} rekaman 'estates' berhasil disinkronkan ke BigQuery.")
        else:
            print(f"[!] Error saat streaming estates ke BigQuery: {errors}")
    else:
        print("[*] Tidak ada data estates lokal untuk disinkronkan.")

def sync_milestones(client, conn):
    from google.cloud import bigquery
    table_id = f"{PROJECT_ID}.{DATASET_ID}.milestones"
    schema = [
        bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("fase", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("nama_fase", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("nomor_urut", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("kode_proses", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("judul", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("kategori", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("waktu_pelaksanaan", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("bulan_mulai", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("bulan_selesai", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("penanggung_jawab", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("output_dokumen", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("deskripsi", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("link_menu", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("link_label", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("rule_pengecekan", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("bobot_persen", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("is_active", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("synced_at", "STRING", mode="NULLABLE")
    ]

    try:
        client.get_table(table_id)
    except Exception:
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)
        print(f"[✓] Tabel BigQuery `{table_id}` berhasil dibuat.")

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ref_roadmap_siklus;")
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]

    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    payload = []
    for r in rows:
        row_dict = dict(zip(cols, r))
        payload.append({
            "id": safe_int(row_dict.get("id")),
            "fase": safe_int(row_dict.get("fase")),
            "nama_fase": safe_str(row_dict.get("nama_fase")),
            "nomor_urut": safe_int(row_dict.get("nomor_urut")),
            "kode_proses": safe_str(row_dict.get("kode_proses")),
            "judul": safe_str(row_dict.get("judul")),
            "kategori": safe_str(row_dict.get("kategori")),
            "waktu_pelaksanaan": safe_str(row_dict.get("waktu_pelaksanaan")),
            "bulan_mulai": safe_int(row_dict.get("bulan_mulai")),
            "bulan_selesai": safe_int(row_dict.get("bulan_selesai")),
            "penanggung_jawab": safe_str(row_dict.get("penanggung_jawab")),
            "output_dokumen": safe_str(row_dict.get("output_dokumen")),
            "deskripsi": safe_str(row_dict.get("deskripsi")),
            "link_menu": safe_str(row_dict.get("link_menu")),
            "link_label": safe_str(row_dict.get("link_label")),
            "rule_pengecekan": safe_str(row_dict.get("rule_pengecekan")),
            "bobot_persen": safe_float(row_dict.get("bobot_persen")),
            "is_active": safe_int(row_dict.get("is_active"), 1),
            "synced_at": now_str
        })

    if payload:
        delete_job = client.query(f"DELETE FROM `{table_id}` WHERE true")
        delete_job.result()
        errors = client.insert_rows_json(table_id, payload)
        if not errors:
            print(f"[✓] SUKSES: {len(payload)} rekaman 'milestones' berhasil disinkronkan ke BigQuery.")
        else:
            print(f"[!] Error saat streaming milestones ke BigQuery: {errors}")

def sync_audit_logs(client, conn):
    from google.cloud import bigquery
    table_id = f"{PROJECT_ID}.{DATASET_ID}.audit_logs"
    schema = [
        bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("request_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("stand_age", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("land_area", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("crop_type", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("ler_score", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("pls_percentage", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("forest_saved_ha", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("carbon_tco2e", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("sha256_hash", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("client_ip", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("created_at", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("synced_at", "STRING", mode="NULLABLE")
    ]

    try:
        client.get_table(table_id)
    except Exception:
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)
        print(f"[✓] Tabel BigQuery `{table_id}` berhasil dibuat.")

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM compute_audit_logs;")
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]

    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    payload = []
    for r in rows:
        row_dict = dict(zip(cols, r))
        payload.append({
            "id": safe_int(row_dict.get("id")),
            "request_id": safe_str(row_dict.get("request_id")),
            "stand_age": safe_float(row_dict.get("stand_age")),
            "land_area": safe_float(row_dict.get("land_area")),
            "crop_type": safe_str(row_dict.get("crop_type")),
            "ler_score": safe_float(row_dict.get("ler_score")),
            "pls_percentage": safe_float(row_dict.get("pls_percentage")),
            "forest_saved_ha": safe_float(row_dict.get("forest_saved_ha")),
            "carbon_tco2e": safe_float(row_dict.get("carbon_tco2e")),
            "sha256_hash": safe_str(row_dict.get("sha256_hash")),
            "client_ip": safe_str(row_dict.get("client_ip")),
            "created_at": safe_str(row_dict.get("created_at")),
            "synced_at": now_str
        })

    if payload:
        delete_job = client.query(f"DELETE FROM `{table_id}` WHERE true")
        delete_job.result()
        errors = client.insert_rows_json(table_id, payload)
        if not errors:
            print(f"[✓] SUKSES: {len(payload)} rekaman 'audit_logs' berhasil disinkronkan ke BigQuery.")
        else:
            print(f"[!] Error saat streaming audit_logs ke BigQuery: {errors}")
    else:
        print("[*] Tidak ada audit_logs lokal.")

def sync_node_audit_reviews(client, conn):
    from google.cloud import bigquery
    table_id = f"{PROJECT_ID}.{DATASET_ID}.node_audit_reviews"
    schema = [
        bigquery.SchemaField("node_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("node_title", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("estate_code", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("verdict_answer", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("citations", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("citations_json", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("sha256_hash", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("timestamp", "STRING", mode="NULLABLE")
    ]

    try:
        client.get_table(table_id)
    except Exception:
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)
        print(f"[✓] Tabel BigQuery `{table_id}` berhasil dibuat.")

    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(node_audit_reviews);")
    existing_cols = [c[1] for c in cursor.fetchall()]
    if not existing_cols:
        print("[*] Tabel node_audit_reviews belum ada di SQLite lokal.")
        return

    cursor.execute("SELECT node_id, estate_code, node_title, verdict_answer, citations_json, timestamp, sha256_hash FROM node_audit_reviews;")
    rows = cursor.fetchall()
    payload = []
    for r in rows:
        payload.append({
            "node_id": safe_str(r[0]),
            "estate_code": safe_str(r[1]),
            "node_title": safe_str(r[2]),
            "verdict_answer": safe_str(r[3]),
            "citations": safe_str(r[4]),
            "citations_json": safe_str(r[4]),
            "timestamp": safe_str(r[5]),
            "sha256_hash": safe_str(r[6])
        })

    if payload:
        errors = client.insert_rows_json(table_id, payload)
        if not errors:
            print(f"[✓] SUKSES: {len(payload)} rekaman 'node_audit_reviews' berhasil disinkronkan ke BigQuery.")
        else:
            print(f"[!] Error saat streaming node_audit_reviews ke BigQuery: {errors}")
    else:
        print("[*] Tidak ada node_audit_reviews lokal.")

def sync_milestone_audit_trail(client, conn):
    from google.cloud import bigquery
    table_id = f"{PROJECT_ID}.{DATASET_ID}.milestone_audit_trail"
    schema = [
        bigquery.SchemaField("id", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("timestamp", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("kode_kebun", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("step_code", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("status", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("sha256_seal", "STRING", mode="NULLABLE")
    ]

    try:
        client.get_table(table_id)
    except Exception:
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)
        print(f"[✓] Tabel BigQuery `{table_id}` berhasil dibuat.")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, timestamp, kode_kebun, step_code, status, sha256_seal FROM milestone_audit_trail;")
        rows = cursor.fetchall()
    except Exception:
        rows = []

    payload = []
    for r in rows:
        payload.append({
            "id": safe_int(r[0]),
            "timestamp": safe_str(r[1]),
            "kode_kebun": safe_str(r[2]),
            "step_code": safe_str(r[3]),
            "status": safe_str(r[4]),
            "sha256_seal": safe_str(r[5])
        })

    if payload:
        errors = client.insert_rows_json(table_id, payload)
        if not errors:
            print(f"[✓] SUKSES: {len(payload)} rekaman 'milestone_audit_trail' berhasil disinkronkan ke BigQuery.")
        else:
            print(f"[!] Error saat streaming milestone_audit_trail ke BigQuery: {errors}")
    else:
        print("[*] Tidak ada milestone_audit_trail lokal.")

def main():
    print("=" * 65)
    print("   PRECISION PALM - SQLITE TO BIGQUERY LEDGER SYNC")
    print(f"   Target Project: {PROJECT_ID}")
    print(f"   Target Dataset: {DATASET_ID}")
    print(f"   Database Path : {DB_PATH}")
    print("=" * 65)

    if not os.path.exists(DB_PATH):
        print(f"[!] File database {DB_PATH} tidak ditemukan.")
        sys.exit(1)

    client = get_bq_client()
    if not client:
        sys.exit(1)

    if not ensure_dataset(client):
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    try:
        sync_estates(client, conn)
        sync_milestones(client, conn)
        sync_audit_logs(client, conn)
        sync_node_audit_reviews(client, conn)
        sync_milestone_audit_trail(client, conn)
        print("=" * 65)
        print("[✓] Seluruh sinkronisasi data ke BigQuery Ledger selesai dengan sempurna.")
        print("=" * 65)
    finally:
        conn.close()

if __name__ == '__main__':
    main()

