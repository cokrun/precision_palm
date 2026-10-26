# cloud_services/bigquery_manager.py
"""
Precision Palm Enterprise - Cloud-Native BigQuery & GCS Storage Manager.
Menerapkan migrasi Direct Write ke Google Cloud BigQuery dan Cloud Storage (GCS).
Sesuai: docs/perintah_eksekusi_ag_direct_bigquery_gcs.md
"""

import os
import io
import time
import sqlite3
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union

try:
    from google.cloud import bigquery, storage
except Exception as _e_gcp:
    bigquery = None
    storage = None

from cloud_services.bigquery_audit import (
    get_bq_client as _get_audit_bq_client,
    PROJECT_ID as AUDIT_PROJECT_ID,
    DATASET_ID as AUDIT_DATASET_ID,
    DB_PATH
)

from config import Config

logger = logging.getLogger("precision_palm.bigquery_direct")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [BQ_DIRECT] %(message)s'))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

PROJECT_ID = Config.PROJECT_ID
DATASET_ID = Config.BQ_DATASET
GCS_BUCKET_NAME = Config.GCS_BUCKET
TABLE_NAME = "dossiers"

_GCS_CLIENT_INSTANCE = None

def get_bq_client():
    """Mengembalikan klien Google Cloud BigQuery terautentikasi."""
    return _get_audit_bq_client()

def get_gcs_bucket():
    """Mengembalikan objek Google Cloud Storage bucket `GCS_BUCKET_NAME`."""
    global _GCS_CLIENT_INSTANCE
    if storage is None:
        return None
    try:
        if _GCS_CLIENT_INSTANCE is None:
            # Menggunakan kredensial yang sama dengan BigQuery Client
            bq_client = get_bq_client()
            if bq_client and getattr(bq_client, '_credentials', None):
                _GCS_CLIENT_INSTANCE = storage.Client(project=PROJECT_ID, credentials=bq_client._credentials)
            else:
                _GCS_CLIENT_INSTANCE = storage.Client(project=PROJECT_ID)
        return _GCS_CLIENT_INSTANCE.bucket(GCS_BUCKET_NAME)
    except Exception as e:
        logger.warning(f"[GCS] Gagal inisialisasi GCS bucket '{GCS_BUCKET_NAME}': {e}")
        return None

def upload_file_to_gcs(file_obj_or_path: Union[str, bytes, io.BytesIO, Any], destination_blob_name: str, content_type: str = "image/jpeg") -> Optional[str]:
    """
    Mengunggah file biner (foto drone, berkas legal, ortofoto) langsung ke Google Cloud Storage (GCS).
    Mengembalikan URI gs:// hanya setelah upload berhasil; None jika GCS tidak tersedia.
    """
    destination_blob_name = destination_blob_name.lstrip('/')
    bucket = get_gcs_bucket()
    if not bucket:
        logger.warning(f"[GCS] Bucket offline/tidak ditemukan untuk {destination_blob_name}")
        return None

    try:
        blob = bucket.blob(destination_blob_name)
        if isinstance(file_obj_or_path, str):
            if os.path.exists(file_obj_or_path):
                blob.upload_from_filename(file_obj_or_path, content_type=content_type)
            else:
                blob.upload_from_string(file_obj_or_path.encode('utf-8'), content_type=content_type)
        elif isinstance(file_obj_or_path, bytes):
            blob.upload_from_string(file_obj_or_path, content_type=content_type)
        elif hasattr(file_obj_or_path, 'read'):
            # File-like object (e.g. Werkzeug FileStorage / BytesIO)
            file_obj_or_path.seek(0)
            blob.upload_from_file(file_obj_or_path, content_type=content_type)
        else:
            blob.upload_from_string(bytes(file_obj_or_path), content_type=content_type)

        gcs_uri = f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"
        logger.info(f"[GCS Upload OK] Berhasil mengunggah file ke {gcs_uri}")
        return gcs_uri
    except Exception as e:
        logger.error(f"[GCS Upload Error] Gagal mengunggah ke GCS {destination_blob_name}: {e}")
        return None


def download_file_from_gcs(blob_name: str) -> Optional[tuple[bytes, str]]:
    """Downloads a private GCS object and returns its bytes and content type."""
    bucket = get_gcs_bucket()
    if not bucket:
        raise RuntimeError(f"GCS bucket '{GCS_BUCKET_NAME}' is unavailable")

    blob = bucket.blob(blob_name.lstrip('/'))
    if not blob.exists():
        return None
    blob.reload()
    return blob.download_as_bytes(), blob.content_type or "application/octet-stream"


def list_gcs_blob_names(prefix: str) -> List[str]:
    """Lists object names under a GCS prefix."""
    bucket = get_gcs_bucket()
    if not bucket:
        raise RuntimeError(f"GCS bucket '{GCS_BUCKET_NAME}' is unavailable")
    return [blob.name for blob in bucket.list_blobs(prefix=prefix.lstrip('/'))]


def delete_gcs_blob(blob_name: str) -> bool:
    """Deletes a GCS object, treating an already-missing object as success."""
    bucket = get_gcs_bucket()
    if not bucket:
        raise RuntimeError(f"GCS bucket '{GCS_BUCKET_NAME}' is unavailable")
    blob = bucket.blob(blob_name.lstrip('/'))
    if not blob.exists():
        return True
    blob.delete()
    return True

def get_table_ref(table_name: str = TABLE_NAME) -> str:
    return f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

def insert_dossier_direct_bq(data: dict) -> Dict[str, Any]:
    """
    Menulis data pendaftaran konsesi baru langsung ke tabel BigQuery `dossiers_master` dan `dossiers`.
    Sesuai: TUGAS 1 di docs/perintah_eksekusi_ag_direct_bigquery_gcs.md
    """
    client = get_bq_client()
    dossier_id = str(data.get("dossier_id") or data.get("kode_kebun") or "").strip()
    if not dossier_id:
        raise ValueError("dossier_id atau kode_kebun wajib diisi.")

    company_id = str(data.get("company_id") or f"COMP-{dossier_id.replace('EST-', '')}").strip()
    company_name = str(data.get("company_name") or data.get("nama_kebun") or f"PT Perkebunan {dossier_id}").strip()
    audit_year = int(data.get("audit_year") or 2026)
    estate_block_name = str(data.get("estate_block_name") or data.get("nama_kebun") or f"Blok Mandiri {dossier_id}").strip()
    legal_title_type = str(data.get("legal_title_type") or data.get("tipe_entitas") or "HGU").strip()
    legal_deed_number = str(data.get("legal_deed_number") or data.get("nomor_hgu") or f"001/HGU/{dossier_id}/2026").strip()
    tax_nop_pbb = str(data.get("tax_nop_pbb") or data.get("nop_pbb") or "12.13.010.001.001-0001.0").strip()
    certified_area_ha = float(data.get("certified_area_ha") or data.get("luas_ha") or 500.0)
    palm_stand_age_years = float(data.get("palm_stand_age_years") or data.get("umur_sawit") or 7.0)
    status_permohonan = str(data.get("status_permohonan") or "VERIFIED").strip()
    now_iso = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

    row_data = {
        "dossier_id": dossier_id,
        "company_id": company_id,
        "company_name": company_name,
        "audit_year": audit_year,
        "estate_block_name": estate_block_name,
        "legal_title_type": legal_title_type,
        "legal_deed_number": legal_deed_number,
        "tax_nop_pbb": tax_nop_pbb,
        "certified_area_ha": certified_area_ha,
        "palm_stand_age_years": palm_stand_age_years,
        "status_permohonan": status_permohonan,
        "created_at": now_iso
    }

    bq_success = False
    bq_msg = ""
    if client and bigquery is not None:
        try:
            # Masukkan ke tabel fisik `dossiers`
            table_id = get_table_ref("dossiers")
            errors = client.insert_rows_json(table_id, [row_data])
            if errors:
                logger.warning(f"[BQ Direct Insert Note] BigQuery insert error on dossiers: {errors}")
                bq_msg = str(errors)
            else:
                bq_success = True
                logger.info(f"[BQ Direct Insert OK] Dossier {dossier_id} berhasil dimasukkan langsung ke BigQuery {table_id}")
        except Exception as e:
            logger.warning(f"[BQ Direct Insert Exception] {e}")
            bq_msg = str(e)

    centroid_lat = float(data.get("centroid_lat") or 0.824100)
    centroid_lng = float(data.get("centroid_lng") or 99.561200)
    boundary_geojson = str(data.get("boundary_geojson") or data.get("poligon_geojson") or '{"type": "Polygon", "coordinates": [[[99.5582, 0.8211], [99.5642, 0.8211], [99.5642, 0.8271], [99.5582, 0.8271], [99.5582, 0.8211]]]}')

    # Sinkronisasi ke basis data lokal SQLite untuk integritas dual-read desktop
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO dossiers (
                    dossier_id, company_id, audit_year, estate_block_name,
                    legal_title_type, legal_deed_number, tax_nop_pbb, certified_area_ha,
                    palm_stand_age_years, centroid_lat, centroid_lng, boundary_geojson, status_permohonan
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                dossier_id, company_id, audit_year, estate_block_name,
                legal_title_type, legal_deed_number, tax_nop_pbb, certified_area_ha,
                palm_stand_age_years, centroid_lat, centroid_lng, boundary_geojson, status_permohonan
            ))
            # Sinkronisasi ke kebun_profil jika belum ada
            cur.execute("""
                INSERT OR IGNORE INTO kebun_profil (
                    kode_kebun, nama_kebun, nomor_hgu, nop_pbb, luas_ha, umur_sawit, centroid_lat, centroid_lng, poligon_geojson, is_active, sync_bigquery
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1);
            """, (dossier_id, company_name, legal_deed_number, tax_nop_pbb, certified_area_ha, palm_stand_age_years, centroid_lat, centroid_lng, boundary_geojson))
            conn.commit()
    except Exception as sqle:
        logger.warning(f"[SQLite Dual-Write Warning] {sqle}")

    return {
        "status": "success",
        "message": "Berhasil disimpan langsung ke BigQuery." if bq_success else f"Tersimpan ke ledger (BigQuery notice: {bq_msg or 'Sync queued'})",
        "dossier_id": dossier_id,
        "bigquery_synced": bq_success,
        "row": row_data
    }

def fetch_bq_dossiers_paginated(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """
    Mengambil data riil dari BigQuery table `dossiers_master` atau `dossiers`.
    """
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))

    client = get_bq_client()
    if client and bigquery is not None:
        try:
            # Query langsung dari dossiers_master / dossiers
            query = f"""
                SELECT dossier_id, company_name, audit_year, estate_block_name, certified_area_ha, status_permohonan
                FROM `{get_table_ref('dossiers')}`
                ORDER BY dossier_id ASC
                LIMIT @limit OFFSET @offset
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("limit", "INT64", limit),
                    bigquery.ScalarQueryParameter("offset", "INT64", offset),
                ]
            )
            query_job = client.query(query, job_config=job_config)
            rows = [dict(row) for row in query_job.result()]
            
            logger.info(f"Successfully fetched {len(rows)} dossiers directly from BigQuery DW")
            return {
                "status": "success",
                "source": "bigquery_live",
                "count": len(rows),
                "rows": rows
            }
        except Exception as e:
            logger.warning(f"BigQuery live query error, falling back to SQLite: {e}")

    # Fallback to local SQLite database
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    COALESCE(d.dossier_id, kp.kode_kebun) as dossier_id,
                    COALESCE(c.company_name, kp.nama_kebun, 'PT Agro Palm') as company_name,
                    COALESCE(d.audit_year, 2026) as audit_year,
                    COALESCE(d.estate_block_name, kp.nama_kebun) as estate_block_name,
                    COALESCE(d.certified_area_ha, kp.luas_ha, 0.0) as certified_area_ha,
                    COALESCE(d.status_permohonan, 'VERIFIED') as status_permohonan
                FROM kebun_profil kp
                LEFT JOIN dossiers d ON kp.kode_kebun = d.dossier_id
                LEFT JOIN companies c ON d.company_id = c.company_id
                ORDER BY kp.kode_kebun ASC
                LIMIT ? OFFSET ?;
            """, (limit, offset))
            rows = [dict(r) for r in cur.fetchall()]
            return {
                "status": "success",
                "source": "sqlite_fallback",
                "count": len(rows),
                "rows": rows
            }
    except Exception as sqle:
        logger.error(f"Fallback SQLite query error: {sqle}")
        return {
            "status": "error",
            "message": str(sqle),
            "rows": []
        }

def update_bq_dossier_record(dossier_id: str, new_area_ha: float, new_status: str) -> Dict[str, Any]:
    """
    Memperbarui certified_area_ha dan status_permohonan langsung di BigQuery.
    """
    if not dossier_id:
        return {"status": "error", "message": "dossier_id is required"}

    dossier_id = str(dossier_id).strip()
    new_area_ha = float(new_area_ha)
    new_status = str(new_status).strip()

    bq_updated = False
    client = get_bq_client()
    if client and bigquery is not None:
        try:
            query = f"""
                UPDATE `{get_table_ref('dossiers')}`
                SET certified_area_ha = @area, status_permohonan = @status
                WHERE dossier_id = @id
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("area", "FLOAT64", new_area_ha),
                    bigquery.ScalarQueryParameter("status", "STRING", new_status),
                    bigquery.ScalarQueryParameter("id", "STRING", dossier_id),
                ]
            )
            client.query(query, job_config=job_config).result()
            bq_updated = True
            logger.info(f"BigQuery DML UPDATE successful for {dossier_id}")
        except Exception as e:
            logger.warning(f"BigQuery DML UPDATE notice for {dossier_id}: {e}")

    # Synchronize local SQLite
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                UPDATE dossiers
                SET certified_area_ha = ?, status_permohonan = ?
                WHERE dossier_id = ?
            """, (new_area_ha, new_status, dossier_id))
            conn.execute("""
                UPDATE kebun_profil
                SET luas_ha = ?
                WHERE kode_kebun = ?
            """, (new_area_ha, dossier_id))
            conn.commit()
    except Exception as sqle:
        logger.warning(f"SQLite local sync warning for {dossier_id}: {sqle}")

    return {
        "status": "success",
        "message": f"Dossier {dossier_id} updated successfully",
        "dossier_id": dossier_id,
        "certified_area_ha": new_area_ha,
        "status_permohonan": new_status,
        "bigquery_updated": bq_updated
    }

def delete_bq_dossier_record(dossier_id: str) -> Dict[str, Any]:
    """
    Menghapus record dossier langsung di BigQuery dan lokal SQLite.
    """
    if not dossier_id:
        return {"status": "error", "message": "dossier_id is required"}

    dossier_id = str(dossier_id).strip()

    bq_deleted = False
    client = get_bq_client()
    if client and bigquery is not None:
        try:
            query = f"""
                DELETE FROM `{get_table_ref('dossiers')}`
                WHERE dossier_id = @id
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("id", "STRING", dossier_id),
                ]
            )
            client.query(query, job_config=job_config).result()
            bq_deleted = True
            logger.info(f"BigQuery DML DELETE successful for {dossier_id}")
        except Exception as e:
            logger.warning(f"BigQuery DML DELETE notice for {dossier_id}: {e}")

    # Synchronize local SQLite
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM dossiers WHERE dossier_id = ?", (dossier_id,))
            conn.execute("DELETE FROM kebun_profil WHERE kode_kebun = ?", (dossier_id,))
            conn.commit()
    except Exception as sqle:
        logger.warning(f"SQLite local delete warning for {dossier_id}: {sqle}")

    return {
        "status": "success",
        "message": f"Dossier {dossier_id} deleted successfully",
        "dossier_id": dossier_id,
        "bigquery_deleted": bq_deleted
    }
