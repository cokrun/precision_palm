# INSTRUKSI EKSEKUSI RESMI UNTUK AG: INTEGRASI MANAJEMEN CRUD BIGQUERY DI APLIKASI

**Perihal:** Pendaftaran Endpoint API BigQuery (`/api/bq/dossiers`, `/api/bq/dossier/update`, `/api/bq/dossier/delete`) serta Halaman Manajer `/bigquery-manager`.

---

## 📌 RINGKASAN PERINTAH KERJA (OBJECTIVES)
1. **Tambahkan Rute di `app.py`:**
   - Daftarkan endpoint `GET /api/bq/dossiers` yang memanggil `fetch_bq_dossiers_paginated()` dari `cloud_services/bigquery_manager.py`.
   - Daftarkan endpoint `POST /api/bq/dossier/update` untuk melakukan sunting (*edit*) baris di BigQuery.
   - Daftarkan endpoint `POST /api/bq/dossier/delete` untuk menghapus (*delete*) baris di BigQuery.
   - Daftarkan rute `GET /bigquery-manager` untuk merender `templates/bigquery_admin.html`.
2. **Uji Fungsionalitas:**
   - Buka `http://localhost:8080/bigquery-manager` di browser untuk melihat tabel riil BigQuery, mengedit luas/status, atau menghapus catatan.

---

## 🛠️ KODE PENDUKUNG UNTUK `app.py`:

```python
@app.route('/bigquery-manager')
def bigquery_manager_page():
    return render_template('bigquery_admin.html')

@app.route('/api/bq/dossiers', methods=['GET'])
def api_bq_get_dossiers():
    from cloud_services.bigquery_manager import fetch_bq_dossiers_paginated
    return jsonify(fetch_bq_dossiers_paginated(limit=50, offset=0))

@app.route('/api/bq/dossier/update', methods=['POST'])
def api_bq_update_dossier():
    from cloud_services.bigquery_manager import update_bq_dossier_record
    data = request.get_json() or {}
    res = update_bq_dossier_record(
        dossier_id=data.get('dossier_id'),
        new_area_ha=float(data.get('certified_area_ha', 0)),
        new_status=data.get('status_permohonan', 'VERIFIED')
    )
    return jsonify(res)

@app.route('/api/bq/dossier/delete', methods=['POST'])
def api_bq_delete_dossier():
    from cloud_services.bigquery_manager import delete_bq_dossier_record
    data = request.get_json() or {}
    res = delete_bq_dossier_record(dossier_id=data.get('dossier_id'))
    return jsonify(res)