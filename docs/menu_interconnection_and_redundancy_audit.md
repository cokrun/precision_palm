# AUDIT FORENSIK BERKAS, KETERKAITAN MENU & ANJURAN ELIMINASI DUPLIKASI
**Sistem:** Precision Palm — Biophysical Agroforestry Intelligence  
**Status:** Audit & Rekomendasi Eksekusi Bersih (Zero-Redundancy & Zero-Mockup)

---

## 1. RINGKASAN REKOMENDASI PENGHAPUSAN (DELETE RECOMMENDATIONS)

| No | Berkas | Status Audit | Alasan & Analisis Kode | Tindakan Disarankan |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `templates/ai-logs.htm` | **DUPLIKAT PERSIS** | Berkas ini 100% identik biner dan baris per baris dengan `ai-logs.html` dan `log_ai.html`. Ekstensi `.htm` tidak lazim dalam konvensi Jinja2 Flask. | **HAPUS (`rm templates/ai-logs.htm`)** |
| 2 | `templates/ai-logs.html` vs `templates/log_ai.html` | **REDUNDAN (NAMA GANDA)** | Rute Flask di `app.py` me-render `render_template('log_ai.html')` untuk rute `/ai-logs`. Keberadaan `ai-logs.html` dan `log_ai.html` secara bersamaan membingungkan pengembang. | **PILIH SATU:** Pertahankan `templates/log_ai.html` (atau samakan rute Flask ke `ai-logs.html`), lalu **HAPUS yang satunya**. |
| 3 | `templates/guide.html` vs `templates/panduan.html` | **TUMPANG TINDIH KONSEP** | `panduan.html` ditautkan ke menu navigasi `/panduan` (Scientific Manual & SOP Berbasis Peran). Sedangkan `guide.html` adalah prototipe lama/interaktif simulator yang tidak memiliki rute resmi di sidebar utama. | **ARSIPKAN / HAPUS `guide.html`** jika fiturnya telah dilebur ke `/proses_bisnis` atau `/panduan`. |
| 4 | `templates/mapping.html` vs `templates/spatial.html` | **LEGACY (KETINGGALAN ZAMAN)** | `mapping.html` adalah viewer peta statis Leaflet raster lokal lama. Di sistem baru, fitur geospasial resmi telah dipindahkan total ke `templates/spatial.html` (didukung Google Earth Engine API, PIPPIB 2024, Drone HUD, dan Gemini 3.8 Flash). | **HAPUS `templates/mapping.html`** agar tidak membebani ukuran repositori. |

---

## 2. PEMERIKSAAN FILE SATU PER SATU & KETERKAITAN DENGAN MENU

### 1. `templates/pengaturan.html`
* **Keterkaitan Menu:**
  * Terhubung langsung dengan menu sidebar `/pengaturan` (Pusat Kendali Pengaturan Sistem).
  * Mengintegrasikan formula harga TBS dan Indeks K (`rumus_tb.py` / Permentan 33/2025).
  * Mengatur *context switching* Multi-Tenancy (berpindah antara `EST-MDN-001`, `EST-RIAU-002`, `EST-KALTENG-003`).
* **Temuan Mockup / Perbaikan:**
  * Baris 300 di JavaScript: Masih ada array statis `DOSSIERS_DATA = [ { id: "EST-MDN-001", ... }, ... ]`.
  * *Tindakan:* Hubungkan fungsi `renderDossierTable()` langsung ke endpoint `GET /api/estates` atau `GET /api/companies/tenants` agar tabel membaca data riil dari database SQLite WAL.

---

### 2. `templates/about.html`
* **Keterkaitan Menu:**
  * Terhubung dengan rute `/about` di header dan footer ("About Us / System Genesis").
  * Berfungsi sebagai naskah profil arsitektur, tim pengembang, pencatatan HAKI DJKI, dan bukti inferensi mesin GCP Cloud Run.
* **Status Berkas:**
  * **PERTAHANKAN (SAHIH).** Sangat penting untuk kredensial juri kompetisi AI Builder Cup dan verifikasi institusional.
* **Temuan Mockup / Perbaikan:**
  * Pada blok terminal curl (`ESTATE-MADINA-001`), ganti teks statis agar konsisten menggunakan kode kanonikal resmi: `EST-MDN-001`.

---

### 3. `templates/log_ai.html` (dan `ai-logs.html` / `ai-logs.htm`)
* **Keterkaitan Menu:**
  * Terhubung dengan rute `/ai-logs` di sidebar / top bar.
  * Menampilkan buku besar telemetri transaksi mesin Google Gemini 3.8 Flash, ekspor PDF transaksi, dan latensi komputasi live.
* **Status Berkas:**
  * **Hapus `ai-logs.htm`**.
  * Satukan menjadi `templates/log_ai.html` sebagai *single source of truth*.
* **Temuan Mockup / Perbaikan:**
  * Script JavaScript di dalamnya sudah sangat baik dan murni terhubung ke endpoint `/api/ai/logs?limit=500` dan `/api/ai/test-ping`.

---

### 4. `templates/audit_report.html`
* **Keterkaitan Menu:**
  * Terhubung secara dinamis via tombol "Print Audit Report" atau "Inspect Deliverable" dari modul Roadmap (`/roadmap`) dan Validasi Publik (`/validasi`).
  * Menggunakan Jinja2 templating: `{{ record.nomor_registrasi }}`, `{{ total_ler }}`, `{{ climate_tco2e }}`.
* **Status Berkas:**
  * **PERTAHANKAN (SAHIH).** Merupakan dokumen resmi luaran audit (lampiran teknis sertifikat).
* **Temuan Mockup / Perbaikan:**
  * Baris 249: Nilai default hash digital masih tertulis `"8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4"`.
  * *Tindakan:* Pastikan parameter `digital_signature` selalu diisi dari kolom `certification_audits.immutable_dossier_sha256` dari backend.

---

### 5. `templates/certificate.html`
* **Keterkaitan Menu:**
  * Terhubung dengan rute `/certificate/<id_permohonan>` dan tombol "View Certificate" di Roadmap.
  * Berfungsi sebagai Paspor Kepatuhan Statuter Resmi (EUDR TRACES-NT & ISPO) siap cetak A4.
* **Status Berkas:**
  * **PERTAHANKAN (SAHIH & KRUSIAL).** Dokumen pamungkas dari seluruh alur 4-tahap sertifikasi.
* **Temuan Mockup / Perbaikan:**
  * Pastikan QR code mengarah dinamis ke URL publik deployment saat ini (`https://precision-palm-...run.app/validasi/{{ record.nomor_registrasi }}`), bukan domain localhost mati.

---

### 6. `templates/panduan.html`
* **Keterkaitan Menu:**
  * Terhubung dengan menu utama `/panduan` di header dan sidebar ("Panduan Ilmiah & SOP").
  * Memuat penurunan matematis Monsi-Saeki (Beer-Lambert), LER Mead & Willey, SCS-CN Eko-hidrologi, serta SOP berdasarkan 4 peran operasional (Mandor, Agronomis, Auditor, Manajemen).
* **Status Berkas:**
  * **PERTAHANKAN (SAHIH).** Merupakan manual operasional resmi.

---

### 7. `templates/guide.html`
* **Keterkaitan Menu:**
  * Merupakan simulator interaktif step-by-step 6 tahap berbasis audio-visual dan animasi confetti.
  * Sebagian besar konten menduplikasi apa yang sudah disajikan secara lebih aplikatif di `/proses_bisnis`, `/roadmap`, dan `/panduan`.
* **Rekomendasi:**
  * Jika menu sidebar tidak lagi memuat tautan `/guide`, berkas ini dapat diarsipkan atau **dihapus** untuk merampingkan ukuran bundle aplikasi di Cloud Run.

---

### 8. `templates/mapping.html`
* **Keterkaitan Menu:**
  * Prototipe Leaflet MBTiles lama.
  * Rute utama untuk peta telah beralih ke `templates/spatial.html` (`/spatial`).
* **Rekomendasi:**
  * **HAPUS.** Seluruh fungsionalitas peta satelit, audit poligon, dan verifikasi PIPPIB telah diimplementasikan secara mutakhir di `templates/spatial.html`.

---

## 3. CHECKLIST PERINTAH EKSEKUSI PEMBERSIHAN (UNTUK TERMINAL / AG)

Jalankan perintah berikut di terminal project untuk membersihkan file redundan:

```bash
# 1. Hapus file duplikat biner dan ekstensi tidak standar
rm -f templates/ai-logs.htm

# 2. Hapus prototipe mapping lama (sudah digantikan oleh templates/spatial.html)
rm -f templates/mapping.html

# 3. Konsolidasi log AI (pilih salah satu nama standar di Flask)
# Jika di app.py menggunakan log_ai.html:
rm -f templates/ai-logs.html