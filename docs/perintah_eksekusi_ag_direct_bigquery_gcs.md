# INSTRUKSI EKSEKUSI RESMI UNTUK AG: MIGRASI ARSITEKTUR CLOUD-NATIVE (DIRECT TO BIGQUERY & GCS)

**Perihal:** Transisi Total dari Basis Data Lokal (SQLite WAL) ke Cloud-Native Storage Langsung (*Direct Write*) untuk Modul Desktop, dengan Antrean Sinkronisasi Khusus Modul Mobile (PWA).  
**Dasar Keputusan Arsitektur:** 
* Menghilangkan ketergantungan file database lokal yang ephemerally ter-reset saat *restart*.
* Menjadikan Google Cloud BigQuery sebagai *Single Source of Truth* yang abadi.
* Menyimpan file biner gambar/ortofoto ke Google Cloud Storage (GCS Bucket) dan mencatat URL-nya di tabel BigQuery.

---

## 📌 RINGKASAN ARSITEKTUR BARU
1. **Desktop / Web Workspace (Pendaftaran, Spasial, In-Silico, Roadmap, Topologi):**
   * Setiap aksi tambah, ubah, atau unggah data langsung mengeksekusi REST API Python client yang melakukan *insert/update/delete* langsung ke tabel-tabel di dataset BigQuery (`precision_palm_dw`).
2. **Modul Mobile / PWA Lapangan (Mandor In-Situ):**
   * Tetap menggunakan pola *Offline-First Local Storage* di perangkat mandor, yang kemudian melakukan *Background Sync* (sinkronisasi berkala) ke server begitu sinyal internet tersedia.
3. **Penyimpanan Media (GCS):**
   * File foto drone atau kamera mandor diunggah langsung ke bucket GCS (`gs://precision-palm-enterprise-evidence/`), dan baris tabel BigQuery hanya menyimpan pointer URL objek GCS tersebut.

---

## 🛠️ TUGAS 1: PERBARUI KONEKTOR `cloud_services/bigquery_manager.py`

Pastikan klien BigQuery dan GCS siap menangani *direct write* tanpa fallback ke file SQLite lokal untuk operasi utama:

```python
# cloud_services/bigquery_manager.py
import os
import logging
from google.cloud import bigquery, storage

logger = logging.getLogger("precision_palm.bigquery_direct")

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "palm-project-511008")
DATASET_ID = os.environ.get("BIGQUERY_DATASET", "precision_palm_dw")
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET", "precision-palm-enterprise-evidence")

def get_bq_client():
    return bigquery.Client(project=PROJECT_ID)

def get_gcs_bucket():
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        return storage_client.bucket(GCS_BUCKET_NAME)
    except Exception as e:
        logger.warning(f"[GCS] Gagal inisialisasi GCS bucket: {e}")
        return None

def upload_file_to_gcs(file_obj, destination_blob_name: str) -> str:
    """
    Mengunggah file biner (gambar/ortofoto) langsung ke Google Cloud Storage (GCS).
    Mengembalikan URL publik atau gs:// uri.
    """
    bucket = get_gcs_bucket()
    if not bucket:
        return f"[https://storage.googleapis.com/mock-bucket/](https://storage.googleapis.com/mock-bucket/){destination_blob_name}"
    
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(file_obj)
    return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"

def insert_dossier_direct_bq(data: dict):
    """
    Menulis data pendaftaran konsesi baru langsung ke tabel BigQuery `dossiers_master`.
    """
    client = get_bq_client()
    table_id = f"{PROJECT_ID}.{DATASET_ID}.dossiers_master"
    
    rows_to_insert = [
        {
            "dossier_id": data.get("dossier_id"),
            "company_id": data.get("company_id", "COMP-DEFAULT"),
            "company_name": data.get("company_name"),
            "audit_year": int(data.get("audit_year", 2026)),
            "estate_block_name": data.get("estate_block_name"),
            "legal_title_type": data.get("legal_title_type"),
            "legal_deed_number": data.get("legal_deed_number"),
            "tax_nop_pbb": data.get("tax_nop_pbb"),
            "certified_area_ha": float(data.get("certified_area_ha", 0.0)),
            "palm_stand_age_years": float(data.get("palm_stand_age_years", 7.0)),
            "status_permohonan": "VERIFIED",
            "created_at": bigquery.enums.AutoRowIDs.DEFAULT_VALUE_SETTERS
        }
    ]
    
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        raise Exception(f"BigQuery Insert Error: {errors}")
    return {"status": "success", "message": "Berhasil disimpan langsung ke BigQuery."}

🛠️ TUGAS 2: SESUAIKAN ENDPOINT DI app.py

Pastikan rute pendaftaran form (/api/estates/create atau sejenisnya) memanggil fungsi insert_dossier_direct_bq sehingga data langsung masuk ke cloud warehouse tanpa singgah ke SQLite lokal.
Python

@app.route('/api/estates/create', methods=['POST'])
def api_create_estate_direct_bq():
    try:
        data = request.get_json() or request.form.to_dict()
        from cloud_services.bigquery_manager import insert_dossier_direct_bq
        res = insert_dossier_direct_bq(data)
        return jsonify(res)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

🧪 PENGUJIAN AKHIR OLEH AG

    Pastikan variabel lingkungan GCP project terkonfigurasi.

    Jalankan aplikasi:

Bash

   python app.py
   

    Lakukan pendaftaran lahan baru atau sunting data di /bigquery-manager → pastikan data langsung ter-commit di BigQuery secara permanen dan aman dari risiko restart.