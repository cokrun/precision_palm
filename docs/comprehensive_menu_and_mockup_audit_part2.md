# LAPORAN AUDIT TAHAP 2: KETERKAITAN MENU, MOCKUP TERSEMBUNYI & ANJURAN ELIMINASI DUPLIKASI

**Sistem:** Precision Palm — Enterprise Biophysical Agroforestry Intelligence  
**Cakupan Berkas:**
1. `templates/validasi.html`
2. `templates/pendaftaran_2.html` vs `templates/pendaftaran.html`
3. `templates/slide.html` vs `templates/slide_deck.html` vs `templates/slides.html`
4. `templates/proses_bisnis.html`
5. `templates/teknologi.html`

---

## 1. RINGKASAN ANJURAN PENGHAPUSAN BERKAS (DELETION DIRECTIVE)

| No | Berkas Target | Status Analisis | Fakta Kode & Redundansi | Rekomendasi Tindakan |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `templates/slide.html` | **WRAPPER KOSONG (1 BARIS)** | Hanya berisi `{% include 'slides.html' %}`. Rute Flask di `app.py` sudah langsung memanggil `slides.html`. | **HAPUS (`rm templates/slide.html`)** |
| **2** | `templates/slide_deck.html` | **DUPLIKAT LAMA (DEPRECATED)** | Berkas ini adalah versi lama sebelum penambahan modal cetak PDF multi-halaman pada `templates/slides.html`. | **HAPUS (`rm templates/slide_deck.html`)** |
| **3** | `templates/pendaftaran_2.html` | **BERKAS BACKUP/DUPLIKAT** | Menggandakan `templates/pendaftaran.html` dengan sedikit modifikasi script. Di dalam proyek MVC Flask hanya boleh ada satu `pendaftaran.html`. | **HAPUS (`rm templates/pendaftaran_2.html`)** |

---

## 2. AUDIT RINCI BERKAS & MOCKUP TERSEMBUNYI SATU PER SATU

---

### A. `templates/validasi.html` (Portal Validasi Publik QR Paspor)

#### 1. Keterkaitan Menu & Arsitektur
* **Rute URL:** `/validasi/<id_sertifikat>` (contoh: `/validasi/CERT-ECOGREEN-2026-0001` atau `/validasi/EST-MDN-001`).
* **Keterkaitan Menu:**
  * Dibuka saat pembeli CPO internasional, auditor pelabuhan, atau regulator memindai QR Code pada sertifikat fisik / digital.
  * Tautannya juga tersedia pada tombol di halaman `certificate.html`, `roadmap.html`, dan `audit_report.html`.
* **Kualitas Backend:** Sangat baik, mengadopsi kontrol status dinamis (`lifecycle.is_suspended`, `lifecycle.status_code`, `lifecycle.quarterly_timeline`).

#### 2. Mockup Tersembunyi & Titik Perbaikan
* **Baris 236–243:**  
  Tabel surveilans mandor memiliki kolom status:
  
```html
  <span class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
      ✓ Satellite Match
  </span>
  
Status "✓ Satellite Match" dan "VERIFIED AI" ditulis statis di dalam loop {% for log in monitoring_logs %} tanpa membaca kolom log.weather_satellite_validation dari database.Perbaikan:Ganti dengan nilai dinamis:Cuplikan kode  {% if log.weather_satellite_validation == 'MATCH_BMKG_RADAR_CLEAR' %}
      <span class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">✓ BMKG Matched</span>
  {% else %}
      <span class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-950 text-amber-300 border border-amber-800">⚠ Pending Audit</span>
  {% endif %}
  
Status Berkas: PERTAHANKAN (SAHIH & WAJIB).B. templates/pendaftaran_2.html (vs templates/pendaftaran.html)1. Keterkaitan MenuRute resmi di app.py merender render_template('pendaftaran.html').Berkas pendaftaran_2.html tidak dipanggil oleh menu navigasi manapun di sidebar atau header.2. Temuan Mockup di pendaftaran_2.htmlBaris 248–268 (FALLBACK_MORATORIUM_COORDS):Masih menyimpan koordinat poligon moratorium keras (hardcoded).Baris 638–647 (isEstateForestCollision):JavaScript  function isEstateForestCollision(lat, lng, kode = null) {
      if (kode === 'EST-MDN-005') return true;
      ...
  }
  
Status pelanggaran dikunci manual khusus untuk EST-MDN-005. Jika pengguna mengunggah kebun lain yang menabrak batas hutan, fungsi ini tidak otomatis mendeteksinya jika backend tidak mengirim data spasial.Tindakan:HAPUS templates/pendaftaran_2.html. Pastikan perbaikan tanpa hardcoded diterapkan pada satu-satunya file induk: templates/pendaftaran.html.C. templates/proses_bisnis.html (Interactive Video Storyboard)1. Keterkaitan MenuRute URL: /proses_bisnis.Keterkaitan Menu: Terhubung langsung pada sidebar dan header ("Storyboard Alur Bisnis / Video Simulator").Berfungsi sebagai panduan 8 adegan animasi untuk demonstrasi proses ujung-ke-ujung bagi juri kompetisi AI Builder Cup dan investor.2. Temuan Mockup / KeterbatasanBaris 380–500 (Array SCENES_DATA):Data skrip narasi dan ilustrasi 8 adegan memang sengaja diletakkan di JavaScript frontend sebagai media presentasi mandiri. Ini bukan bug, melainkan curated presentation script.Baris 548 (fetchGeminiTtsAudio):JavaScript  const apiKey = "";
  if (!apiKey) {
      throw new Error("No Gemini API key provided; falling back to enhanced speech synthesis");
  }
  
API key sengaja dikosongkan untuk keamanan agar tidak terekspos di browser client, lalu otomatis melakukan fallback ke playExecutiveWebSpeech() (Web Speech API).Rekomendasi:Tambahkan endpoint proxy backend: POST /api/ai/tts di app.py agar permintaan audio TTS dieksekusi di server menggunakan secret GEMINI_API_KEY internal GCP, bukan memanggil endpoint Google langsung dari browser.Status Berkas: PERTAHANKAN (SAHIH & SANGAT INTERAKTIF).D. templates/slides.html (vs slide.html & slide_deck.html)1. Keterkaitan MenuRute URL: /slides.Terhubung pada menu "Executive Slide Deck" di header dan landing page.Memiliki 10 slide interaktif (16:9 widescreen) dengan dukungan dwibahasa (EN/ID), kontrol keyboard, gestur layar sentuh, dan modul cetak PDF A4 landscape multi-halaman.2. Analisis Redundansitemplates/slide.html: Hanya 1 baris include. (HAPUS)templates/slide_deck.html: Versi duplikat usang tanpa modal cetak PDF. (HAPUS)templates/slides.html: Versi terlengkap dan termutakhir. (PERTAHANKAN)3. Status BerkasPERTAHANKAN templates/slides.html.E. templates/teknologi.html (Enterprise Architecture Whitepaper)1. Keterkaitan MenuRute URL: /teknologi.Terhubung pada menu "Teknologi GCP / Whitepaper" di footer dan header.Memuat dokumentasi teknis mendalam tentang integrasi 6 layanan Google Cloud AI & GEE:Vertex AI (Gemini 3.8 Flash)Document AI (Deed Parser)Google Earth Engine (GEE API)Cloud Speech-to-Text (Chirp 2)Vertex AI Search GroundingBigQuery ML (ARIMA Time-Series)2. Temuan Mockup / Inkonsistensi Penamaan ModelBaris 242:Judul kartu menuliskan Google Vertex AI & Gemini 3.8 Flash, namun di bagian metadata baris 251 tertulis:HTML  <span data-i18n="tek_card1_meta1">Model: gemini-2.5-flash</span>
  
Model lama gemini-2.5-flash masih tertinggal di metadata kartu.Perbaikan:Ubah metadata teks menjadi Model: gemini-3.8-flash agar selaras di seluruh dokumen.Status Berkas: PERTAHANKAN (SAHIH).3. CHECKLIST PERINTAH EKSEKUSI PEMBERSIHAN (TERMINAL / AG)Jalankan perintah berikut di terminal project untuk membersihkan file duplikat:Bash# 1. Hapus file wrapper dan duplikat slide
rm -f templates/slide.html
rm -f templates/slide_deck.html

# 2. Hapus file pendaftaran cadangan
rm -f templates/pendaftaran_2.html
4. MATRIKS HUBUNGAN MENU & TEMPLATE TERAKHIR (SETELAH SANITASI)Rute URL FlaskBerkas Template AktifFungsi Utama di MenuStatus/index.htmlBeranda, KPI Nasional & Visi MakroAktif/pendaftaranpendaftaran.htmlTahap 1: Direktori Berkas & Peta Konsesi WGS84Aktif/permohonanpermohonan.htmlTahap 1: Pendaftaran Baru & Document AIAktif/spatialspatial.htmlTahap 2A: GEE Satelit, PIPPIB & KelerenganAktif/prosessimulator.htmlTahap 2B: In-Silico Beer-Lambert, LER & PasporAktif/timelinestimelines.htmlTahap 3: Surveilans 4 Triwulan & MandorAktif/mobilemobile/index.htmlTahap 3: Node PWA Mandor Luring & Chirp 2Aktif/roadmaproadmap.htmlTahap 4: All-Report Master Dossier & SidangAktif/topologitopologi.htmlSilsilah Proses: 12-Node DAG & Grounded AIAktif/certificate/<id>certificate.htmlPaspor Kepatuhan Statuter Resmi (A4)Aktif/validasi/<id>validasi.htmlPortal Validasi Publik QR Paspor EUDR/ISPOAktif/pengaturanpengaturan.htmlPusat Kendali Sistem, Harga TBS & Multi-TenantAktif/ai-logslog_ai.htmlTelemetri Mesin Gemini 3.8 Flash LiveAktif/panduanpanduan.htmlPanduan Ilmiah, Formulasi Matematis & SOPAktif/teknologiteknologi.htmlWhitepaper Arsitektur GCP & Tolok Ukur LatensiAktif/proses_bisnisproses_bisnis.htmlStoryboard Alur Bisnis 8 AdeganAktif/slidesslides.htmlSlide Presentasi Eksekutif (10 Slide)Aktif/aboutabout.htmlProfil Genesis, Tim Pengembang & HAKI DJKI Aktif