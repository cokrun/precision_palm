# DIRECTIVE RESMI AG: PEMBERSIHAN TOTAL ASET FOTO STATIS (PURGE STATIC FALLBACKS) & MIGRASI KE DATABASE STREAMING MURNI

**Status:** Perintah Pembersihan Kode Wajib (Mandatory Code Cleanup)  
**Target:** Menghapus seluruh kemunculan file statis `sawit_drone.jpg`, `field_tm_weed.jpg`, `field_wetland_buffer.jpg`, array `ref_photos`, dan file JSON mockup `precision_store.json`.

---

## 1. TEMUAN MASALAH DI `app.py` (BARIS 521–532)

Pada fungsi `get_all_estate_photos_list(store)`:
```python
# KODE LAMA YANG RUSAK (MOCKUP/DUMMY SCRIPT):
# 4. Standard reference photos
ref_photos = [
    {"filename": "sawit_drone.jpg", "file_url": "/static/img/sawit_drone.jpg", ...},
    {"filename": "field_tm_weed.jpg", "file_url": "/static/img/field_tm_weed.jpg", ...},
    {"filename": "field_wetland_buffer.jpg", "file_url": "/static/img/field_wetland_buffer.jpg", ...}
]
for rp in ref_photos:
    if rp['file_url'] not in seen_urls:
        photos.append(rp)

Dampak Kerusakan:
Bagian ini secara paksa menyuntikkan 3 foto statis ke dalam galeri foto perkebunan mana pun, bahkan untuk perkebunan baru yang belum pernah diaudit. Akibatnya, data riil dari database tertutup oleh foto-foto pajangan ini.
2. ATURAN PENGGANTIAN MURNI (DATABASE-DRIVEN REPLACEMENT)
A. Ubah get_all_estate_photos_list di app.py Menjadi Kueri SQL Murni

Hapus ref_photos dan store.get('field_tracking', []). Ganti fungsi tersebut dengan kueri ke tabel inspection_evidence:
Python

# STREAMING_CHUNK:Replacing hardcoded photos with pure SQLite WAL query
def get_all_estate_photos_list(dossier_id: str, audit_year: int = 2026) -> list:
    """
    Mengambil daftar foto bukti inspeksi MURNI dari database SQLite WAL.
    Jika belum ada foto yang diunggah, mengembalikan list KOSONG ([]).
    TIDAK BOLEH menyuntikkan ref_photos palsu!
    """
    from database_schema_engine import get_db_connection
    conn = get_db_connection()
    photos = []
    try:
        rows = conn.execute("""
            SELECT 
                evidence_id,
                dossier_id,
                quarter_cycle,
                perspective_mode,
                uploaded_at,
                image_sha256_hash,
                detected_entities_json
            FROM inspection_evidence
            WHERE dossier_id = ? AND audit_year = ?
            ORDER BY uploaded_at DESC;
        """, (dossier_id, audit_year)).fetchall()

        for r in rows:
            photos.append({
                "id": r["evidence_id"],
                "filename": f"{r['evidence_id']}.jpg",
                "file_url": f"/api/media/evidence/{r['evidence_id']}",
                "title": f"Inspeksi {r['quarter_cycle']} • {r['perspective_mode']}",
                "tag": r["quarter_cycle"],
                "sha256": r["image_sha256_hash"],
                "uploaded_at": r["uploaded_at"]
            })
        return photos
    finally:
        conn.close()

B. Bersihkan database.py dari Path Statis

Periksa seluruh baris di database.py yang memuat:
"/static/img/field_tm_weed.jpg" atau "/static/img/sawit_drone.jpg".

    Ganti nilai kolom foto_url di database menjadi: f"/api/media/evidence/{evidence_id}".

    Simpan data biner foto asli ke kolom image_raw_base64 dan hash ke image_sha256_hash.

C. Hapus File Mockup precision_store.json

    Hapus file precision_store.json atau kosongkan isinya.

    Hapus pemanggilan init_local_store() dan write_local_store().

    Seluruh data operasional kebun bersumber mutlak dari precision_palm.db.

D. Tampilan Antarmuka Frontend (Empty State)

Jika get_all_estate_photos_list mengembalikan list kosong []:

    Tampilkan blok HTML status kosong di template:

HTML

<div class="p-8 text-center bg-slate-900/60 rounded-2xl border border-slate-800 text-slate-400 font-mono text-xs">
    <span>📷</span>
    <p class="mt-2 text-white font-bold">Belum ada foto inspeksi lapangan untuk berkas ini.</p>
    <p class="text-slate-500 text-[11px] mt-1">Silakan lakukan pengambilan foto in-situ melalui modul Mobile PWA (/mobile).</p>
</div>

    DILARANG menampilkan tag <img src="/static/img/..."> sebagai gambar cadangan.

Cuplikan kode


Tangkapan layar Anda membongkar baris kode `ref_photos` di baris 521–532 `app.py`:
```python
# 4. Standard reference photos
ref_photos = [
    {"filename": "sawit_drone.jpg", "file_url": "/static/img/sawit_drone.jpg", ...},
    {"filename": "field_tm_weed.jpg", "file_url": "/static/img/field_tm_weed.jpg", ...},
    {"filename": "field_wetland_buffer.jpg", "file_url": "/static/img/field_wetland_buffer.jpg", ...}
]

Blok kode di atas sengaja menyisipkan 3 foto statis ke dalam daftar foto kebun mana pun secara paksa, sehingga data kebun baru tetap memunculkan foto yang sama.
