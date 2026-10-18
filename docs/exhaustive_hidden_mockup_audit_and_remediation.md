# LAPORAN AUDIT LENGKAP: TEMUAN MOCKUP TERSEMBUNYI & RENCANA PERBAIKAN

**Klasifikasi:** Audit Forensik Kode Sumber (Zero-Mockup Strict Policy)  
**Tujuan:** Mengeliminasi seluruh sisa fallback palsu, nilai statis hardcoded, dan data sintetis pada seluruh modul Mobile PWA dan script pemicu AI.

---

## 1. TEMUAN DI `mobile/js/mobile_camera.js`

### A. Titik Cacat:
1. **Baris 20–39 (`DEFAULT_PALM_DIAGNOSTICS`):**
   
```javascript
   const DEFAULT_PALM_DIAGNOSTICS = {
       estimated_age_years: 7.5,
       growth_stage: "Tanaman Menghasilkan (TM)",
       foliar_health: {
           chlorosis_status: "NORMAL / HEALTHY",
           foliar_chlorophyll_spad: 82.4, ...
       }, ...
   };
   

    Masalah: Jika mandor memotret kebun baru di Riau (EST-RIAU-002) saat offline, sistem menampilkan hasil diagnosa palsu 82.4 SPAD dan umur 7.5 tahun milik Mandailing Natal!

    Baris 41–50 (REAL_PHYSICAL_ENTITIES):

JavaScript

   const REAL_PHYSICAL_ENTITIES = [
       { id: "obj_01", label: "Palm Trunk Left", cluster: "palm_anatomy", box_2d: [210, 110, 890, 310], confidence: 0.98 },
       ...
   ];
   

    Masalah: 8 kotak koordinat ini adalah mockup statis yang akan menggantung di atas foto apa pun yang diambil mandor jika API AI offline.

    Baris 186–218 (triggerAiVisionAnalysis):
    Terdapat variabel fallback yang mengkloning data palsu di atas:

JavaScript

   const fallbackPhysicalEntities = [ ... ];
   const fallbackDiag = { ... };
   

B. Solusi Perbaikan:

    Hapus konstanta DEFAULT_PALM_DIAGNOSTICS dan REAL_PHYSICAL_ENTITIES.

    Jika backend AI gagal merespons atau sedang offline:

        Kotak deteksi diset kosong murni: boxes = [].

        Status telemetri diset ke status tunggu: "Menunggu sinkronisasi AI saat online".

        Jangan pernah menggambar bounding box palsu di kanvas!

2. TEMUAN DI mobile/js/mobile_db.js
A. Titik Cacat:

    Baris 60–75 (loadEstatesFromBackend):

JavaScript

   if (registeredEstatesList.length === 0) {
       registeredEstatesList = [
           {
               id: 1, id_kebun: 1, kode_kebun: "EST-MDN-001",
               nama_kebun: "PT Mandailing Agro Sustainable", ...
           },
           {
               id: 2, id_kebun: 2, kode_kebun: "EST-MDN-002", ...
           }
       ];
   }
   

    Masalah: Jika koneksi API /api/estates terputus, aplikasi otomatis memunculkan 2 kebun Mandailing Natal buatan ke dropdown.

B. Solusi Perbaikan:

    Jika API gagal, ambil dari IndexedDB store estates_cache.

    Jika IndexedDB masih kosong, biarkan dropdown kosong atau tampilkan satu opsi: "(Belum ada kebun di-cache, sambungkan internet untuk unduh awal)".

3. TEMUAN DI mobile/js/mobile_gps.js
A. Titik Cacat:

    Baris 13–24 (liveCoordinates):

JavaScript

   let liveCoordinates = {
       lat: 0.824100,
       lng: 99.561200,
       elev: 142.0,
       ground_elev: 142.0,
       accuracy: 4.5,
       weather: "26.6°C Cerah Berawan", ...
   };
   

    Masalah: Koordinat dan cuaca default di-set keras ke Mandailing Natal. Jika GPS perangkat mandor belum terkunci, aplikasi mengirimkan lokasi palsu ini ke server.

    Baris 102–104 (updateWeatherSatellite):

JavaScript

   liveCoordinates.weather = isId ? "26.6°C Cerah Berawan (BMKG)" : "26.6°C Partly Cloudy (Satellite)";
   

    Masalah: Teks cuaca sintetis disuntikkan jika Open-Meteo offline.

B. Solusi Perbaikan:

    Set koordinat awal ke null atau NaN (lat: null, lng: null, elev: null).

    Tampilkan teks di UI: "[Menunggu Kunci Satelit GPS]" sampai sensor navigator.geolocation benar-benar memberikan koordinat riil.

    Jika cuaca offline, tampilkan: "[Data Cuaca Offline]".

4. TEMUAN DI mobile/index.html
A. Titik Cacat:

    Baris 108:

HTML

   <option value="EST-MDN-010">EST-MDN-010 • PT Mandailing Agro Sustainable</option>
   

    Masalah: Menuliskan kebun EST-MDN-010 langsung di markup HTML.

    Baris 140–160:

HTML

   <strong id="valDispLat">0.824100</strong>
   <strong id="valDispLng">99.561200</strong>
   <strong id="valDispElev">142m DPL</strong>
   <strong id="valDispWeather">26.6°C Cerah Berawan</strong>
   <input type="text" id="inpBlockId" value="Blok A - Gawangan #1">
   <input type="text" id="inpMandorName" value="Mandor Sutrisno">
   

    Masalah: Semua teks dan input bernilai bawaan statis.

    Baris 178–184:

HTML

   <img id="viewfinderPhotoImg" src="/api/media/evidence/current?dossier_id=EST-MDN-001&perspective=TERRESTRIAL_IN_SITU" ...>
   

    Masalah: Parameter dossier_id=EST-MDN-001 tertulis mati di HTML.

B. Solusi Perbaikan:

    Kosongkan isi <option> dan nilai <input> (biarkan diisi dinamis oleh JavaScript berdasarkan dossier aktif).

    Ganti dossier_id=EST-MDN-001 pada tag <img> agar membaca parameter URL aktif atau kosongkan jika dossier belum memiliki foto.

5. TEMUAN DI static/js/global_ai_triggers.js & static/js/gemini_audit.js
A. Titik Cacat:

    global_ai_triggers.js (Baris 21–23):

JavaScript

   const lat = document.getElementById('inpLat')?.value || "0.824100";
   const lng = document.getElementById('inpLng')?.value || "99.561200";
   

    gemini_audit.js (Baris 19):

JavaScript

   const concessionId = document.getElementById('inp_nomor_hgu')?.value || "EST-MDN-001";
   

B. Solusi Perbaikan:

    Jangan menggunakan fallback hardcoded "0.824100", "99.561200", atau "EST-MDN-001".

    Ambil nilai dari input yang aktif atau variabel global currentActiveEstateCode. Jika tidak ditemukan, hentikan proses dan minta pengguna memilih kebun terlebih dahulu.

6. CHECKLIST PERBAIKAN UNTUK AG

    [x] mobile_camera.js: Hapus DEFAULT_PALM_DIAGNOSTICS & REAL_PHYSICAL_ENTITIES. Jangan render box palsu saat offline.

    [x] mobile_db.js: Hapus array dummy fallback registeredEstatesList (MDN-001 & MDN-002).

    [x] mobile_gps.js: Inisialisasi koordinat dengan null. Hapus teks cuaca sintetis "26.6°C Cerah Berawan".

    [x] mobile/index.html: Kosongkan nilai hardcoded pada input form, dropdown, dan tag <img>.

    [x] global_ai_triggers.js: Hapus fallback "0.824100" dan "99.561200".

    [x] gemini_audit.js: Hapus fallback "EST-MDN-001".