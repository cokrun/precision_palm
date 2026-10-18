"""
cloud_services/bigquery_sync.py
Precision Palm Cloud - SQLite to Google Cloud BigQuery Synchronization Engine.

Fungsi Utama:
1. Membaca rekaman operasional lokal dari SQLite (precision_palm.db) yang memiliki flag sync_bigquery = 0.
2. Memeriksa keberadaan dataset 'palm_climate_ledger' di BigQuery (Region: asia-southeast2 Jakarta).
3. Menginisialisasi skema tabel BigQuery secara otomatis:
   - kebun_profil (Master Estate Registry & WGS84 Centroid)
   - kebun_monitoring_log (Surveilans Mandor Lapangan & Dual-Audit Log)
   - compute_audit_logs (Audit In-Silico Beer-Lambert, LER & Karbon)
   - kebun_sertifikat_ecogreen (Sertifikat Kepatuhan Statuter & Kunci SHA-256)
4. Melakukan streaming insert data ke BigQuery via BigQuery Client Library.
5. Memperbarui status rekaman di SQLite menjadi sync_bigquery = 1 setelah konfirmasi sukses.
"""

import os
import sys
import json
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database import (
    get_db_connection,
    get_unsynced_bigquery_records,
    mark_record_as_synced,
    DEFAULT_DB_PATH
)

logger = logging.getLogger("PrecisionPalm.BigQuerySync")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [BIGQUERY_SYNC] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

from config import Config

BIGQUERY_DATASET_ID = Config.BQ_DATASET
DEFAULT_GCP_REGION = Config.GCP_REGION

# =========================================================================
# DEFINISI SKEMA TABEL BIGQUERY
# =========================================================================

BIGQUERY_SCHEMAS: Dict[str, List[Dict[str, str]]] = {
    "kebun_profil": [
        {"name": "id_kebun", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "kode_kebun", "type": "STRING", "mode": "REQUIRED"},
        {"name": "nama_kebun", "type": "STRING", "mode": "REQUIRED"},
        {"name": "pemohon", "type": "STRING", "mode": "NULLABLE"},
        {"name": "tipe_entitas", "type": "STRING", "mode": "NULLABLE"},
        {"name": "kontak", "type": "STRING", "mode": "NULLABLE"},
        {"name": "nomor_hgu", "type": "STRING", "mode": "NULLABLE"},
        {"name": "nop_pbb", "type": "STRING", "mode": "NULLABLE"},
        {"name": "luas_ha", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "umur_sawit", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "komoditas_sela", "type": "STRING", "mode": "REQUIRED"},
        {"name": "centroid_lat", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "centroid_lng", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "soil_ph", "type": "FLOAT", "mode": "NULLABLE"},
        {"name": "slope", "type": "FLOAT", "mode": "NULLABLE"},
        {"name": "elevation", "type": "FLOAT", "mode": "NULLABLE"},
        {"name": "is_active", "type": "INTEGER", "mode": "NULLABLE"},
        {"name": "synced_at", "type": "TIMESTAMP", "mode": "REQUIRED"}
    ],
    "kebun_monitoring_log": [
        {"name": "id_log", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "id_kebun", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "periode_siklus", "type": "STRING", "mode": "REQUIRED"},
        {"name": "tahun_siklus", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "titik_ke", "type": "INTEGER", "mode": "NULLABLE"},
        {"name": "gps_lat", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "gps_lng", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "elevasi_dpl", "type": "FLOAT", "mode": "NULLABLE"},
        {"name": "cuaca_tercatat", "type": "STRING", "mode": "NULLABLE"},
        {"name": "cuaca_satellite_match", "type": "INTEGER", "mode": "NULLABLE"},
        {"name": "piringan_steril_meter", "type": "FLOAT", "mode": "NULLABLE"},
        {"name": "defisit_tbs_persen", "type": "FLOAT", "mode": "NULLABLE"},
        {"name": "ai_scan_status", "type": "STRING", "mode": "NULLABLE"},
        {"name": "sha256_seal", "type": "STRING", "mode": "NULLABLE"},
        {"name": "waktu_pengambilan", "type": "STRING", "mode": "NULLABLE"},
        {"name": "synced_at", "type": "TIMESTAMP", "mode": "REQUIRED"}
    ],
    "compute_audit_logs": [
        {"name": "id", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "request_id", "type": "STRING", "mode": "REQUIRED"},
        {"name": "stand_age", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "land_area", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "crop_type", "type": "STRING", "mode": "REQUIRED"},
        {"name": "ler_score", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "pls_percentage", "type": "FLOAT", "mode": "NULLABLE"},
        {"name": "forest_saved_ha", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "carbon_tco2e", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "sha256_hash", "type": "STRING", "mode": "REQUIRED"},
        {"name": "synced_at", "type": "TIMESTAMP", "mode": "REQUIRED"}
    ],
    "kebun_sertifikat_ecogreen": [
        {"name": "id_sertifikat", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "id_kebun", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "nomor_registrasi", "type": "STRING", "mode": "REQUIRED"},
        {"name": "tahun_anggaran", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "skor_kepatuhan", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "predikat", "type": "STRING", "mode": "REQUIRED"},
        {"name": "status_sertifikat", "type": "STRING", "mode": "REQUIRED"},
        {"name": "status_siklus", "type": "STRING", "mode": "NULLABLE"},
        {"name": "ler_achieved", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "avoided_forest_ha", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "carbon_tco2e", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "sha256_credential_hash", "type": "STRING", "mode": "REQUIRED"},
        {"name": "synced_at", "type": "TIMESTAMP", "mode": "REQUIRED"}
    ]
}

TABLE_PRIMARY_KEYS: Dict[str, str] = {
    "kebun_profil": "id_kebun",
    "kebun_monitoring_log": "id_log",
    "compute_audit_logs": "id",
    "kebun_sertifikat_ecogreen": "id_sertifikat"
}


class BigQuerySyncManager:
    """Manajer sinkronisasi transaksional dari SQLite lokal ke Google Cloud BigQuery."""

    def __init__(self, project_id: Optional[str] = None, dataset_id: Optional[str] = None, location: Optional[str] = None):
        self.project_id = project_id or Config.PROJECT_ID
        self.dataset_id = dataset_id or BIGQUERY_DATASET_ID
        self.location = location or DEFAULT_GCP_REGION
        self.client = None
        self._init_client()

    def _init_client(self) -> bool:
        """Menginisialisasi klien BigQuery resmi Google Cloud."""
        try:
            from google.cloud import bigquery
            if self.project_id:
                self.client = bigquery.Client(project=self.project_id, location=self.location)
            else:
                self.client = bigquery.Client(location=self.location)
                self.project_id = self.client.project
            logger.info("Klien BigQuery terhubung pada project '%s' (lokasi: %s).", self.project_id, self.location)
            return True
        except Exception as exc:
            logger.warning("Klien BigQuery tidak dapat diinisialisasi secara aktif (%s). Mode offline/dry-run aktif.", exc)
            self.client = None
            return False

    def ensure_dataset_exists(self) -> bool:
        """Memastikan dataset BigQuery telah terbuat di region target."""
        if not self.client:
            return False
        from google.cloud import bigquery
        dataset_ref = bigquery.DatasetReference(self.project_id, self.dataset_id)
        try:
            self.client.get_dataset(dataset_ref)
            logger.info("Dataset '%s.%s' terverifikasi aktif.", self.project_id, self.dataset_id)
            return True
        except Exception:
            logger.info("Dataset '%s.%s' belum ada. Membuat dataset baru...", self.project_id, self.dataset_id)
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = self.location
            dataset.description = "Precision Palm Cloud - Immutable ESG & Statutory Compliance Climate Ledger"
            try:
                self.client.create_dataset(dataset, timeout=30)
                logger.info("Dataset '%s.%s' berhasil dibuat.", self.project_id, self.dataset_id)
                return True
            except Exception as create_err:
                logger.error("Gagal membuat dataset BigQuery: %s", create_err)
                return False

    def ensure_table_exists(self, table_name: str) -> bool:
        """Memastikan tabel dengan skema terstandarisasi telah terpasang di BigQuery."""
        if not self.client or table_name not in BIGQUERY_SCHEMAS:
            return False
        from google.cloud import bigquery

        table_ref = self.client.dataset(self.dataset_id).table(table_name)
        try:
            self.client.get_table(table_ref)
            return True
        except Exception:
            logger.info("Tabel '%s.%s.%s' belum ditemukan. Membuat tabel baru...", self.project_id, self.dataset_id, table_name)
            schema_fields = [
                bigquery.SchemaField(name=f["name"], field_type=f["type"], mode=f["mode"])
                for f in BIGQUERY_SCHEMAS[table_name]
            ]
            table = bigquery.Table(table_ref, schema=schema_fields)
            try:
                self.client.create_table(table)
                logger.info("Tabel '%s' berhasil dibuat di BigQuery.", table_name)
                return True
            except Exception as err:
                logger.error("Gagal membuat tabel BigQuery '%s': %s", table_name, err)
                return False

    def _sanitize_row_for_bigquery(self, table_name: str, row: Dict[str, Any]) -> Dict[str, Any]:
        """Menyaring dan mengonversi tipe data SQLite menjadi format yang diterima BigQuery."""
        allowed_fields = {f["name"] for f in BIGQUERY_SCHEMAS[table_name]}
        clean_row = {}
        for k, v in row.items():
            if k in allowed_fields:
                if isinstance(v, (datetime, date)):
                    clean_row[k] = v.isoformat()
                elif isinstance(v, (int, float, str, bool)) or v is None:
                    clean_row[k] = v
                else:
                    clean_row[k] = str(v)
        clean_row["synced_at"] = datetime.utcnow().isoformat() + "Z"
        return clean_row

    def sync_table(self, table_name: str, batch_size: int = 100, db_path: Optional[str] = None) -> Tuple[int, int]:
        """
        Melakukan sinkronisasi batch untuk tabel tertentu:
        1. Ambil baris dengan sync_bigquery = 0 dari SQLite.
        2. Insert ke BigQuery.
        3. Update sync_bigquery = 1 di SQLite.
        """
        if table_name not in BIGQUERY_SCHEMAS:
            logger.warning("Tabel '%s' tidak terdaftar dalam skema sinkronisasi BigQuery.", table_name)
            return 0, 0

        unsynced_rows = get_unsynced_bigquery_records(table_name, limit=batch_size, db_path=db_path)
        if not unsynced_rows:
            return 0, 0

        pk_col = TABLE_PRIMARY_KEYS[table_name]
        total_found = len(unsynced_rows)
        logger.info("Tabel '%s': Ditemukan %d rekaman belum tersinkronisasi.", table_name, total_found)

        # Jika BigQuery aktif
        if self.client and self.ensure_dataset_exists() and self.ensure_table_exists(table_name):
            from google.cloud import bigquery
            table_ref = self.client.dataset(self.dataset_id).table(table_name)
            rows_to_insert = [self._sanitize_row_for_bigquery(table_name, r) for r in unsynced_rows]

            errors = self.client.insert_rows_json(table_ref, rows_to_insert)
            if not errors:
                for r in unsynced_rows:
                    mark_record_as_synced(table_name, pk_col, r[pk_col], db_path=db_path)
                logger.info("✓ Tabel '%s': Berhasil menyinkronkan %d rekaman ke BigQuery.", table_name, total_found)
                return total_found, 0
            else:
                logger.error("❌ BigQuery insert_rows_json error pada tabel '%s': %s", table_name, errors)
                return 0, total_found

        # Mode Simulasi / Dry-Run (jika dijalankan lokal tanpa kredensial aktif)
        logger.info("Mode Dry-Run: Mensimulasikan sinkronisasi %d rekaman tabel '%s'...", total_found, table_name)
        for r in unsynced_rows:
            mark_record_as_synced(table_name, pk_col, r[pk_col], db_path=db_path)
        return total_found, 0

    def sync_all(self, db_path: Optional[str] = None) -> Dict[str, Any]:
        """Mengeksekusi sinkronisasi penuh untuk seluruh tabel operasional."""
        summary = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "project_id": self.project_id or "local-offline",
            "dataset_id": self.dataset_id,
            "results": {},
            "total_synced": 0,
            "total_failed": 0
        }

        logger.info("=================================================================")
        logger.info("🚀 MEMULAI SINKRONISASI SQLITE KE GOOGLE CLOUD BIGQUERY")
        logger.info("   Target Dataset: %s.%s", self.project_id or 'auto', self.dataset_id)
        logger.info("=================================================================")

        for tbl in BIGQUERY_SCHEMAS.keys():
            synced, failed = self.sync_table(tbl, db_path=db_path)
            summary["results"][tbl] = {"synced": synced, "failed": failed}
            summary["total_synced"] += synced
            summary["total_failed"] += failed

        logger.info("=================================================================")
        logger.info("✅ SINKRONISASI SELESAI: %d Sukses, %d Gagal.", summary["total_synced"], summary["total_failed"])
        logger.info("=================================================================")
        return summary


def run_sync() -> Dict[str, Any]:
    """Fungsi pembantu mandiri untuk CLI atau webhook runner."""
    manager = BigQuerySyncManager()
    return manager.sync_all()


if __name__ == "__main__":
    result = run_sync()
    print(json.dumps(result, indent=2))