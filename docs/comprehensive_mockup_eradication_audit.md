# LAPORAN AUDIT FORENSIK KODE: ELIMINASI TOTAL DATA TIRUAN (MOCKUP / HARDCODED)
# Target Audit: mobile.html, simulator.html, spatial.html, timelines.html, topologi.html, roadmap.js, simulator.js, spatial.js, app.py
# Standar Mutlak: Zero-Mockup • Pure Database State • Single Source of Truth (SQLite WAL & BigQuery)

---

## 1. FILE: `mobile.html`

### A. Temuan Ranjau Mockup (Harus Dihapus):
1. **Baris 140–156 (`virtualCameraControls`):**
   Tombol tombol sampel statis `selectVirtualImage('field_tm_weed.jpg', ...)`, `selectVirtualImage('sawit_drone2.jpg', ...)`, dan `selectVirtualImage('field_wetland_buffer.jpg', ...)`.
   * *Masalah:* Mandor di lapangan seharusnya memotret kondisi riil kebunnya, bukan memilih gambar pajangan.
2. **Baris 486–491 (`detectedPresetBoxes`):**
   
```javascript
   const detectedPresetBoxes = [
       { label: 'palm_canopy', label_text: 'Palm Stand (6.0y TM)', box_2d: [120, 200, 720, 480], confidence: 0.98 }, ...
   ];
   

    Masalah: Ini adalah array kotak AI palsu yang disuntikkan secara statis ke layar ponsel mandor!

    Baris 628–642 (loadMandailingPreset):
    Fungsi ini memaksakan koordinat lintang 0.824100 dan bujur 99.561200 saat GPS gagal, alih-alih menampilkan status GPS Acquiring.

    Baris 896 (saveToLocalQueue & syncWithCloudServer):
    Terdapat string hash statis palsu:
    hash: '8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4'

        Masalah: Hash SHA-256 dibuat dari teks tiruan, bukan hasil hashing biner riil dari file foto yang dijepret kamera!

B. Tindakan Perbaikan Wajib:

    Matikan tab "Sample Feeds". Buat tab default langsung ke Live Camera (cameraInput).

    Hapus array detectedPresetBoxes. Kotak bounding box hanya boleh digambar dari respons JSON asli POST /api/ai/scan-image atau POST /api/evidence/upload.

    Hash SHA-256 wajib dihitung di sisi browser menggunakan crypto.subtle.digest('SHA-256', arrayBuffer) dari file foto asli yang diambil kamera mandor.

2. FILE: simulator.html
A. Temuan Ranjau Mockup (Harus Dihapus):

    Baris 183–185 (Input Hidden Statis):

HTML

   <input type="hidden" id="image_sample" value="sawit_drone.jpg">
   <input type="hidden" id="selected_image_url" value="/static/img/sawit_drone.jpg">
   

    Masalah: Secara diam-diam mengunci foto ke sawit_drone.jpg.

    Baris 727–780 (CROPS_15_CATALOG):
    Sebagian metrik finansial seperti base_ler: 1.4545 dan price_idr: 25000 di-hardcode di dalam JavaScript client, alih-alih dihitung dari formula rumus_tb.py via endpoint /api/pricing/tbs-calculation.

    Baris 1317–1340 (runDetailedObjectVisionScan):
    Jika pemanggilan AI offline atau gagal, fungsi ini menyuntikkan fallback kotak buatan:

JavaScript

   detectedBoxes = [
       { label: 'palm_tree', label_name: `Oil Palm Stand TM (~${age.toFixed(1)} Yrs)`, box_2d: [70, 0, 727, 287], ... }, ...
   ];
   

    Masalah: Inilah penyebab kotak bounding box tetap muncul melayang meskipun gambarnya gagal dimuat!

B. Tindakan Perbaikan Wajib:

    Hapus input hidden bernilai sawit_drone.jpg. Ambil data citra dari /api/media/evidence/<id> milik dossier_id aktif.

    Hapus seluruh blok fallback detectedBoxes manual di runDetailedObjectVisionScan. Jika tidak ada deteksi AI riil dari server, detectedBoxes = [] dan bersihkan kanvas.

3. FILE: spatial.html
A. Temuan Ranjau Mockup (Harus Dihapus):

    Baris 382–386 (verifPhotoImg):

HTML

   <img id="verifPhotoImg" src="/api/media/evidence/current?dossier_id=EST-MDN-001&perspective=AERIAL_DRONE" ...>
   

Di sini dossier_id di-hardcode ke EST-MDN-001! Jika pengguna memilih EST-RIAU-002, elemen HTML-nya secara default tetap memanggil EST-MDN-001.
2. Baris 486–505 (CANONICAL_ESTATES_ZONING di spatial.js):
Poligon untuk 10 estate di-hardcode dalam JavaScript, bukan ditarik murni dari kolom boundary_geojson pada tabel dossiers.
3. Baris 540–560 (renderInspectionTrackingAndBufferCircles di spatial.js):
Jika data survei kurang dari 3 titik, kode ini membuat koordinat rekayasa (synthetic GPS points):
JavaScript

   const offsets = [
       { dLat: 0.0000, dLng: 0.0000, blok: "Blok A1 - Inti Sentral", ... },
       { dLat: 0.0028, dLng: -0.0035, blok: "Blok B2 - Sempadan Riparian", ... }, ...
   ];
   

    Masalah: Ini adalah pemalsuan titik survei lapangan secara otomatis!

B. Tindakan Perbaikan Wajib:

    Ganti dossier_id=EST-MDN-001 dengan variabel template Jinja2 atau dibaca dinamis dari URL / dropdown aktif.

    Hapus array CANONICAL_ESTATES_ZONING. Baca poligon murni dari tabel database dossiers.boundary_geojson.

    Hapus array offsets sintetis di spatial.js. Jika sebuah kebun baru belum memiliki log survei, tampilkan nol titik survei (Empty State jujur).

4. FILE: timelines.html
A. Temuan Ranjau Mockup (Harus Dihapus):

    Baris 410–445 (TIMELINES_REAL_PHYSICAL_ENTITIES & TIMELINES_DRONE_AERIAL_ENTITIES):
    Terdapat 18 kotak koordinat hardcoded [box_2d: [60, 40, 220, 200], ...] yang ditanam mati di dalam JavaScript!

        Masalah: Inilah biang kerok mengapa pada tangkapan layar Anda (gambar_4.jpg), teks menuliskan "No field evidence photo uploaded yet", tetapi 16 kotak hijau dan merah tetap digambar menumpuk di atas kanvas kosong!

    Baris 242–246 (Input Form Mandor):
    Latitude 0.824100, Longitude 99.561200, dan Elevation 142 tertulis sebagai value="..." bawaan formulir HTML.

    Baris 430–480 (Kartu Q1 s/d Q4):
    Nilai-nilai tanggal, defisit 1.22%, dan hash 8F434346... tertulis statis di dalam tag <p> HTML, alih-alih ditarik dari tabel inspection_evidence dan certification_audits.

B. Tindakan Perbaikan Wajib:

    HAPUS TOTAL dua konstanta raksasa: TIMELINES_REAL_PHYSICAL_ENTITIES dan TIMELINES_DRONE_AERIAL_ENTITIES.

    Kotak deteksi hanya boleh digambar jika array detected_entities_json dari database berisi data. Jika database kosong, kanvas wajib bersih melompong.

    Kosongkan value default pada form koordinat mandor dan paksa pengambilan koordinat GPS via navigator geolocation perangkat.

5. FILE: topologi.html & topology_audit_manager.js
A. Temuan Ranjau Mockup (Harus Dihapus):

    Baris 620–830 (PROCESS_NODES_DATA):
    Seluruh 12 simpul memiliki ringkasan hasil audit yang sudah ditulis mati di JavaScript:

JavaScript

   node_1_1: { title: "Document AI Intelligent Extraction", summary: "Document AI successfully parsed...", confidence: "99.4%" }
   node_2_1: { title: "PIPPIB Moratorium & EUDR 2020...", summary: "100% zero deforestation verified...", confidence: "99.8%" }
   

    Masalah: Pengguna belum menjalankan audit, tetapi modal pop-up sudah menampilkan bahwa semua simpul sukses dengan confidence 99.4%! Ini adalah kamuflase visual.

    Baris 435 di topologi.html:

JavaScript

   var bqHash = "SEAL-" + Math.random().toString(36).substring(2, 10).toUpperCase();
   

    Masalah: Hash penutupan audit dibuat menggunakan fungsi acak Math.random(), bukan cryptographic hash dari isi rekaman audit!

B. Tindakan Perbaikan Wajib:

    Hubungkan status simpul Node 1.1 s/d 4.3 dengan tabel system_audit_logs, spatial_telemetry, dan certification_audits.

    Jika simpul belum pernah diaudit untuk dossier aktif tersebut, status simpul WAJIB ABU-ABU (NOT_STARTED), dan pop-up harus menyatakan: "Simpul ini belum dieksekusi untuk tahun buku audit aktif."

    Hapus pembuatan hash palsu Math.random(). Gunakan hash SHA-256 asli dari backend.

6. FILE: roadmap.js
A. Temuan Ranjau Mockup (Harus Dihapus):

    Baris 29–210 (STANDARD_PILLAR_MILESTONES):
    Daftar 8 tonggak capaian (milestones) memiliki properti is_done: true secara default! Akibatnya, setiap kali kebun baru dibuka, sistem langsung menganggap semua pilar legalitas dan audit sudah selesai 100%.

    Baris 248–340 (CANONICAL_ESTATES_SEED):
    Menyimpan data statis untuk EST-MDN-001, EST-MDN-002, EST-MDN-003, dan EST-MDN-005 langsung di dalam file JS client dengan persentase progres buatan (100%, 75%, 50%, 25%).

B. Tindakan Perbaikan Wajib:

    Hapus array CANONICAL_ESTATES_SEED. Ambil status pilar langsung melalui fetch('/api/dossier/<id>/state').

    Status is_done pada setiap milestone dihitung secara matematis di server:

        Pilar 1.1 selesai JIKA kolom legal_deed_number di tabel dossiers terisi.

        Pilar 2.1 selesai JIKA ada rekaman di tabel spatial_telemetry.

        Pilar 3.1 selesai JIKA ada rekaman di tabel inspection_evidence.

        Pilar 4.2 selesai JIKA ada rekaman di tabel certification_audits.

7. FILE: app.py
A. Temuan Ranjau Mockup (Harus Dihapus):

    Baris 243–250 (DEFAULT_ESTATE_TELEMETRY_SEEDS):
    Daftar riwayat simulasi buatan yang otomatis di-inject jika database kosong.

    Baris 190–210 (init_local_store & save_local_store):
    Membaca dan menulis ke file JSON lokal precision_store.json. File ini adalah sumber duplikasi yang sering membuat data tidak sinkron dengan SQLite.

    Baris 780–820 (api_parse_deed_document_ai):

Python

   parsed_entities = {
       "nomor_hgu": "024/HGU/BPN-MDN/2026",
       "nop_pbb": "12.13.010.001.002-0042.0",
       "luas_ha": 200.0, ...
   }
   

    Masalah: Endpoint Document AI mengembalikan dictionary hardcoded, tidak benar-benar membaca file PDF yang diunggah pengguna!

B. Tindakan Perbaikan Wajib:

    Hapus file precision_store.json dan nonaktifkan fungsi read_local_store() serta save_local_store().

    Seluruh operasi app.py dialihkan 100% ke fungsi-fungsi di database_schema_engine.py yang membaca dan menulis langsung ke tabel SQLite WAL murni (precision_palm.db).

    Pada api_parse_deed_document_ai, jika Google Document AI API belum dikonfigurasi kuncinya, kembalikan status 503 Service Unavailable atau minta input manual dari pengguna, BUKAN mengembalikan data HGU palsu nomor 024/HGU/BPN-MDN/2026.