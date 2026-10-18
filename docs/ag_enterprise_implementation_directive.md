# DIRECTIVE RESMI UNTUK AG: MULTI-TENANCY PERUSAHAAN, ANTI-FRAUD FOTO & INTEGRASI DATA ALUR PROSES

Mengacu pada:
1. `docs/enterprise_tenancy_antifraud_business_flow_spec.md` (Spesifikasi Multi-Tenancy, Anti-Fraud, & Alur Data).
2. `docs/storage_pipeline_indexeddb_bigquery_spec.md` (Penyimpanan Murni: IndexedDB -> SQLite -> BigQuery).
3. `docs/autonomous_agent_vision_memory_spec.md` (Matriks 44 Variabel & Deteksi Objek Fisik Nyata).

---

### 1. ATURAN MULTI-TENANCY KETAT (PERUSAHAAN TIDAK BOLEH BERCAMPUR)
- Di `app.py` dan `database.py`:
  * Setiap query penampil foto, telemetri, dan hasil audit **WAJIB** difilter berdasarkan `dossier_id` dan `company_name`.
  * Hentikan perilaku lama yang menampilkan data `EST-MDN-001` untuk semua pendaftar baru. Jika pengguna mendaftarkan perusahaan baru (misal: `EST-RIAU-002`), halaman dashboard, spatial, simulator, dan timelines untuk dossier tersebut harus dimulai dari state kosong (*Empty State*) dan menunggu unggahan data asli dari perusahaan bersangkutan.
  * Sediakan pemilih dossier aktif di header / kontrol panel untuk menguji perpindahan antar-perusahaan secara transparan.

---

### 2. SISTEM ANTI-FRAUD FOTO (ANTI-REPLAY / ZERO RE-USE) KHUSUS `/mobile`
- Di `mobile/index.html` & `mobile/js/mobile_camera.js`:
  * Kunci input kamera pada perangkat keras: `<input type="file" capture="environment" accept="image/*">` (Nonaktifkan galeri file lokal).
  * Sebelum mengirim foto, hitung cincang biner SHA-256 dari file foto.
- Di `app.py` (Endpoint `/api/evidence/upload`):
  * Periksa apakah hash SHA-256 foto tersebut sudah pernah tercatat di tabel `used_photo_hashes` di SQLite atau BigQuery.
  * **JIKA DUPLIKAT:** Kembalikan respon `HTTP 409 Conflict`:
    `{"status": "error", "code": "FRAUD_PHOTO_REUSED", "message": "Bukti foto ini telah terdaftar pada audit sebelumnya. Sesuai Permentan 33/2025, wajib mengambil foto fisik baru di lapangan."}`.
  * **JIKA BARU:** Simpan foto ke database, simpan hash ke `used_photo_hashes`, dan lanjutkan proses AI Vision.

---

### 3. INTEGRASI DATA ANTAR-HALAMAN (/spatial + /mobile -> /proses -> /timelines)
- **Hulu Spasial (`/spatial`):**
  * Data kelerengan SRTM (4.5°), vegetasi Sentinel-2 NDVI (0.784), dan sempadan air (>50m) tersimpan ke tabel database di bawah `dossier_id` aktif.
- **Hulu Mandor (`/mobile`):**
  * Foto asli tersimpan sebagai biner/Base64, hasil diagnosa klorofil daun pelepah-17 (82.4 SPAD), dan status piringan 2.0m steril tersimpan di bawah `dossier_id` aktif.
- **Simulator (`/proses`):**
  * Buat tombol: `⚡ [Ambil Data Lapangan & Spasial Terkini]`.
  * Saat diklik, simulator membaca data kelerengan dari `/spatial` dan klorofil daun dari `/mobile` untuk `dossier_id` tersebut.
  * Menghitung LER (1.48x), pupuk penyeimbang MOP (+75 kg/Ha), dan menyajikan Nalar Bio-Ekologis 4 Lapis.
- **Surveilans (`/timelines`):**
  * Kartu Q1 & Q3 menampilkan bukti foto asli dari `/spatial`.
  * Kartu Q2 & Q4 menampilkan bukti foto asli dari `/mobile`.
  * Seluruh foto ditampilkan secara dinamis dari endpoint streaming database `/api/media/evidence/<evidence_id>`, BUKAN dari file statis `/static/img/...`.
  * Perbarui seluruh teks rujukan hukum menjadi **Permentan No. 33 Tahun 2025**.

---

### 4. PENGUJIAN & VERIFIKASI (SANITY CHECK)
1. Jalankan `python app.py`.
2. Buat dossier baru di `/permohonan` dengan nama perusahaan sembarang (misal: `PT Agro Sawit Sejahtera`).
3. Pastikan halaman `/timelines` dan `/proses` untuk perusahaan baru tersebut tidak menampilkan foto milik `EST-MDN-001`.
4. Buka `/mobile` -> unggah foto -> coba unggah foto yang sama persis kedua kalinya -> pastikan sistem memblokir dengan status Anti-Fraud Reused Photo.
5. Pastikan semua fitur berfungsi tanpa ada error JavaScript di console browser.
