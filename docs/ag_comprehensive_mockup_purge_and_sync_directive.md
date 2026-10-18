# DIRECTIVE RESMI AG: PEMBERSIHAN TOTAL SISA-SISA MOCKUP & DATA SINTETIS PADA SELURUH BERKAS PROSES

**Status:** Perintah Pembersihan Kode & Sanitasi Frontend Wajib (Mandatory Zero-Mockup Purge)  
**Target Berkas:**
1. `templates/pendaftaran.html`
2. `templates/roadmap.html` & `static/js/roadmap.js`
3. `templates/simulator.html` & `static/js/simulator.js`
4. `templates/spatial.html` & `static/js/spatial.js`
5. `templates/timelines.html`
6. `templates/topologi.html` & `static/js/topology_audit_manager.js`

---

## 1. TEMUAN MOCKUP DI `templates/pendaftaran.html`

### Titik Cacat:
1. **Baris 248–275 (`CANONICAL_ESTATES_ZONING`):**
   10 koordinat poligon di-hardcode mati di JavaScript:
   
```javascript
   const CANONICAL_ESTATES_ZONING = {
       "EST-MDN-001": [[99.5580, 0.8280], [99.5720, 0.8280], ...],
       ...
   };
   

    Bahaya: Jika pengguna mendaftarkan kebun baru dari Riau (EST-RIAU-002), poligon tetap dipaksakan membaca koordinat Mandailing Natal.

    Baris 380–435 (initNdviLayer):
    Data NDVI kanopi di-hardcode per kebun:

JavaScript

   const ndviEstatesData = [
       { kode: "EST-MDN-001", ndvi: 0.842, canopy: "89.1%", center: [0.8350, 99.5660], delta: 0.012 }, ...
   ];
   

    Bahaya: Angka NDVI 0.842 dan canopy 89.1% adalah angka buatan (synthetic), bukan hasil kalkulasi satelit Sentinel-2 riil dari tabel spatial_telemetry.

    Baris 545–555 (loadDossiersList):
    Masih membaca cache lokal precision_palm_estates_dossier_cache_v5.

Tindakan Perbaikan:

    Hapus array CANONICAL_ESTATES_ZONING dan ndviEstatesData.

    Data poligon dan nilai NDVI wajib diambil murni dari API backend:
    GET /api/dossier/<kode>/state yang membaca kolom dossiers.boundary_geojson dan spatial_telemetry.sentinel2_ndvi_mean.

2. TEMUAN MOCKUP DI templates/roadmap.html & static/js/roadmap.js
Titik Cacat:

    Baris 29–210 di roadmap.js (STANDARD_PILLAR_MILESTONES):
    Seluruh 8 milestone di-set is_done: true secara default:

JavaScript

   { step_code: "P1.1", ..., is_done: true },
   { step_code: "P1.2", ..., is_done: true }, ...
   

    Bahaya: Setiap kali kebun baru dibuka, kebun tersebut langsung tampak 100% lulus sertifikasi tanpa audit!

    Baris 248–340 di roadmap.js (CANONICAL_ESTATES_SEED):
    Data dummy statis untuk EST-MDN-001, EST-MDN-002, EST-MDN-003, dan EST-MDN-005 disimpan di memory JS klien dengan progress buatan (100%, 75%, 50%, 25%).

    Baris 624 di roadmap.html (simulateRoadmapDocAiDeedParse):
    Menyuntikkan data ekstraksi PDF palsu:

JavaScript

   var fallback = {
       nomor_hgu: "004/HGU/BPN-MDN/2021",
       nop_pbb: "12.13.010.001.001-0001.0",
       nama_kebun: "PT Mandailing Agro Sustainable", ...
   };
   

Tindakan Perbaikan:

    Hapus array CANONICAL_ESTATES_SEED.

    Hapus nilai statis is_done: true pada STANDARD_PILLAR_MILESTONES. Hitung status selesai secara nyata dari database:

        Pilar 1.1: dossiers.legal_deed_number IS NOT NULL

        Pilar 2.1: spatial_telemetry record exists

        Pilar 3.1: inspection_evidence record exists

        Pilar 4.2: certification_audits record exists

    Pada simulateRoadmapDocAiDeedParse, jika API Document AI tidak merespons, tampilkan error atau biarkan form kosong agar pengguna mengisi sendiri, jangan menyuntikkan HGU palsu!

3. TEMUAN MOCKUP DI templates/simulator.html & static/js/simulator.js
Titik Cacat:

    Baris 183–185 di simulator.html:

HTML

   <input type="hidden" id="image_sample" value="sawit_drone.jpg">
   <input type="hidden" id="selected_image_url" value="/static/img/sawit_drone.jpg">
   

    Masalah: Secara tersembunyi mengunci foto ke gambar statis sawit_drone.jpg.

    Baris 530–545 di simulator.js (DEFAULT_ESTATE_TELEMETRY_SEEDS):
    Array riwayat simulasi buatan (ID: 48196, 90258, 5200, dsb.) yang disuntikkan ke tabel riwayat audit jika database kosong.

    Baris 465–490 di simulator.js (runDetailedObjectVisionScan):
    Jika pemanggilan AI offline atau error, kode ini menyuntikkan fallback kotak buatan:

JavaScript

   detectedBoxes = [
       { label: 'palm_tree', label_name: 'Oil Palm Stand TM', box_2d: [70, 0, 727, 287], ... }, ...
   ];
   

    Masalah: Ini yang menyebabkan kotak AI melayang di ruang kosong jika gambarnya gagal dimuat.

Tindakan Perbaikan:

    Hapus input hidden bernilai sawit_drone.jpg. Gambar harus bersumber dari endpoint biner database: /api/media/evidence/<id>.

    Hapus array DEFAULT_ESTATE_TELEMETRY_SEEDS. Jika tabel in_silico_simulations di database kosong, tampilkan Empty State jujur: "Belum ada simulasi in-silico untuk berkas ini."

    Hapus array fallback detectedBoxes. Jika AI gagal memindai, kosongkan bounding box (boxes = []) dan jangan gambar kotak apapun di kanvas.

4. TEMUAN MOCKUP DI templates/spatial.html & static/js/spatial.js
Titik Cacat:

    Baris 382–386 di spatial.html:

HTML

   <img id="verifPhotoImg" src="/api/media/evidence/current?dossier_id=EST-MDN-001&perspective=AERIAL_DRONE" ...>
   

    Masalah: Dossier ID di-hardcode ke EST-MDN-001. Ketika berpindah ke dossier lain, tag src awal tetap mengarah ke kebun lama.

    Baris 330–365 di spatial.js (loadPhotosForActiveDossier):
    Terdapat array droneMockups statis yang menyuntikkan 6 foto lokal secara paksa:

JavaScript

   const droneMockups = [
       { filename: 'sawit-drone4.jpeg', file_url: '/static/img/sawit-drone4.jpeg', ... },
       { filename: 'sawit_drone2.jpg', file_url: '/static/img/sawit_drone2.jpg', ... },
       { filename: 'field_wetland_buffer.jpg', file_url: '/static/img/field_wetland_buffer.jpg', ... }, ...
   ];
   

    Masalah: Inilah penyebab mengapa kebun baru yang belum diaudit tetap menampilkan foto drone orang lain!

Tindakan Perbaikan:

    Ubah dossier_id=EST-MDN-001 menjadi parameter dinamis yang dibaca dari dropdown aktif atau sesi login.

    HAPUS TOTAL array droneMockups. Foto galeri hanya boleh dimuat dari respon endpoint /api/dossier/<id>/evidence-gallery yang mengambil data biner dari tabel inspection_evidence. Jika dossier baru belum punya foto, galeri wajib berstatus Empty State.

5. TEMUAN MOCKUP DI templates/timelines.html
Titik Cacat:

    Baris 195–210 (Formulir Mandor):
    Nilai default koordinat Latitude 0.824100, Longitude 99.561200, dan Elevasi 142 tertulis sebagai nilai statis bawaan formulir HTML:

HTML

   <input type="text" id="inp_gps_lat" value="0.824100" ...>
   <input type="text" id="inp_gps_lng" value="99.561200" ...>
   <input type="number" id="inp_elevasi_dpl" value="142" ...>
   

    Masalah: Mandor di daerah lain (misal Riau / Kalteng) akan mengirimkan koordinat Mandailing Natal jika tidak mengklik tombol GPS.

    Baris 245 di kartu triwulan:
    Teks ✓ 2026-04-12 tertulis statis di HTML untuk Q1, padahal kebun baru belum tentu menyelesaikan Q1 pada tanggal tersebut.

Tindakan Perbaikan:

    Kosongkan value default pada input GPS (value=""), dan buat tombol [ 📍 Ambil Lokasi GPS ] mengisi data koordinat secara otomatis dari sensor perangkat (navigator.geolocation).

    Kartu Q1 s/d Q4 harus membaca tanggal dan status penyegelan dari tabel inspection_evidence melalui endpoint /api/estate/quarterly-status. Jika belum ada foto, tampilkan status "Belum Dimulai" atau "Pending".

6. TEMUAN MOCKUP DI templates/topologi.html & static/js/topology_audit_manager.js
Titik Cacat:

    Baris 620–830 di topologi.html (PROCESS_NODES_DATA):
    Seluruh 12 simpul memiliki hasil audit statis yang sudah ditulis mati di JavaScript dengan klaim:
    confidence: "99.4%", verdict: "Passed".

    Baris 435 di topologi.html:

JavaScript

   var bqHash = "SEAL-" + Math.random().toString(36).substring(2, 10).toUpperCase();
   

    Masalah: Hash audit dibuat menggunakan fungsi acak Math.random(), bukan hash kriptografis SHA-256 riil!

Tindakan Perbaikan:

    Status setiap simpul (Node 1.1 s/d 4.3) wajib ditentukan oleh kueri status database:

        Jika belum ada data: Warnai ABU-ABU (NOT_STARTED).

        Jika ada pelanggaran: Warnai MERAH (VIOLATION).

        Jika lolos: Warnai HIJAU (PASSED).

    Hapus penggunaan Math.random() untuk hash segel. Seluruh segel hash wajib diambil dari kolom certification_audits.immutable_dossier_sha256 atau inspection_evidence.image_sha256_hash.

7. RANGKUMAN URUTAN EKSEKUSI OLEH AG

    Langkah 1 (Eliminasi Konstanta Mockup):
    Hapus CANONICAL_ESTATES_ZONING, ndviEstatesData, CANONICAL_ESTATES_SEED, DEFAULT_ESTATE_TELEMETRY_SEEDS, dan droneMockups.

    Langkah 2 (Pengikatan Kueri Dinamis):
    Pastikan setiap fungsi load* mengambil data murni via fetch() ke endpoint backend (/api/dossier/<id>/state, /api/dossier/<id>/evidence-gallery, /api/estates).

    Langkah 3 (Penegakan Empty State):
    Jika array kembalian kosong, tampilkan pesan: "Belum ada data/bukti untuk berkas ini" dan sembunyikan semua kotak AI / poligon sintetis.

    Langkah 4 (Verifikasi):
    Jalankan python test_db_cli.py dan verifikasi bahwa berpindah ke dossier EST-RIAU-002 menampilkan layar bersih tanpa kebocoran data dari EST-MDN-001.