# Tata Kelola Pemulihan Simulator Biofisika

**Status dokumen:** tata kelola dan catatan implementasi lokal v1  
**Cakupan:** halaman Simulator/In-Silico, kalkulasi deterministik, proyeksi skenario, dan status dossier  
**Prinsip utama:** hasil numerik tidak bergantung pada keluaran AI generatif; status hasil harus mengungkap asal, asumsi, dan kecukupan datanya.

## 1. Tujuan dan batasan

Dokumen ini mengkonsolidasikan prinsip pemulihan Simulator tanpa menginstruksikan penyalinan langsung potongan kode protokol lama. Implementasi harus menggunakan engine kalkulasi sebagai sumber angka, mempertahankan provenance, dan menolak klaim pengukuran atau komitmen audit yang tidak didukung bukti.

AI dapat membantu interpretasi dan rekomendasi. AI bukan sumber angka untuk metrik matematis deterministik, tidak boleh mengisi input wajib yang kosong, dan tidak boleh mengubah hasil kalkulasi engine.

### Status implementasi saat ini

- Preview dan persistensi menghitung ulang melalui backend; formula umur-LAI yang aktif adalah `5.5 / (1 + exp(-0.7 * (umur - 3.5)))`, lalu PAR `1800 * exp(-0.45 * LAI)`.
- Persistensi menggunakan tabel SQLite `compute_audit_logs`. Commit baru berstatus `201 COMMITTED`; replay idempotent `200 COMMITTED`; konflik key/payload `409`; validasi `422`.
- Hash SHA-256 dibuat backend dari canonical JSON yang disimpan dalam transaksi yang sama. Jika hasil commit tidak diketahui, klien mempertahankan key untuk rekonsiliasi; tidak membuat seal atau record ID lokal.
- Output yield yang hanya dimasukkan pengguna berstatus `SCENARIO_PROJECTION` sampai provenance lapangan dapat diverifikasi. Output LER tetap model deterministik dengan `input_status` terpisah.
- BigQuery tidak disinkronkan oleh jalur ini saat ini. Respons menampilkan `cloud_sync.status: NOT_CONFIGURED`; komit lokal tidak boleh disebut sebagai komit BigQuery.
- Tombol aksi pasca-commit membuka dossier lokal. Sertifikat `/certificate/<id>` tidak ditawarkan karena rute tersebut membaca BigQuery dan belum ada bukti sinkronisasi record ini.
- Endpoint belum memiliki autentikasi/otorisasi estate yang diterapkan di jalur Simulator. Ini hanya untuk penggunaan lokal tepercaya dan merupakan blocker sebelum endpoint dipublikasikan/deploy.

## 2. Taksonomi status data empat kategori

Setiap metrik yang ditampilkan atau disimpan harus memiliki tepat satu status utama berikut. Status menyatakan **asal dan tingkat bukti**, bukan apakah nilainya terlihat meyakinkan.

| Status | Definisi | Contoh | Tampilan yang disarankan |
|---|---|---|---|
| `FIELD_MEASURED` | Bukti empiris yang dikumpulkan dari sumber teridentifikasi. Pemberian status ini mensyaratkan jenis instrumen/metode, satuan, waktu, lokasi/blok, dan provenance yang cukup untuk memeriksa data. | Yield TBS dari kartu timbang PKS; curah hujan dari AWS; koordinat dari survei GPS dengan referensi geospasial. | Badge hijau zamrud solid: `bg-emerald-950 text-emerald-400`; label **FIELD MEASURED**. |
| `DETERMINISTIC_MODEL` | Hasil kalkulasi deterministik dari rumus yang terdokumentasi dan input yang tercatat. Hasil rumus bukan pengukuran, meskipun inputnya berasal dari profil kebun. | LAI/PAR Beer-Lambert dari umur tegakan; lebar lorong dari jarak tanam dan buffer; LER dari empat yield yang tersedia. | Badge cyan: `bg-cyan-950 text-cyan-400`; label **DETERMINISTIC MODEL**. |
| `SCENARIO_PROJECTION` | Hasil simulasi dengan satu atau lebih asumsi, parameter regional, harga indikatif, atau input yang dapat diubah; tidak menyatakan realisasi maupun kontrak. | Harga TBS dari parameter System Control; proyeksi finansial; estimasi hidrologi regional; valuasi karbon asumsi. | Badge indigo: `bg-indigo-950 text-indigo-400`; label **SCENARIO / PROJECTION**. |
| `DATA_PENDING` | Input wajib kosong, tidak valid, atau tidak memiliki provenance minimum sehingga metrik tidak dapat dihitung atau tidak layak disajikan. | LER tanpa data panen lengkap; pendapatan tanpa harga dan yield yang layak; hidrologi tanpa input yang diperlukan. | Badge abu-abu: `bg-slate-800 text-slate-400`; label **DATA PENDING**. |

### Aturan penerapan status

1. Label `FIELD_MEASURED` hanya sah bila sumber, waktu, unit, lokasi, dan metode/instrumen dapat ditelusuri. Nilai yang sekadar tersimpan di profil tidak otomatis terverifikasi.
2. Output rumus tetap `DETERMINISTIC_MODEL`, walaupun inputnya `FIELD_MEASURED`. Status input dan status output adalah metadata terpisah.
3. Output dengan satu atau lebih input asumsi/regional/pasar adalah `SCENARIO_PROJECTION`; status ini tidak boleh dinaikkan menjadi `DETERMINISTIC_MODEL` hanya karena perhitungannya deterministik.
4. Bila input wajib tidak lengkap atau tidak valid, gunakan `DATA_PENDING` dan jelaskan field yang dibutuhkan. Jangan mengubahnya menjadi nol, memakai angka default tersembunyi, atau mempertahankan hasil lama.
5. Status harus konsisten pada UI, API, dossier yang disimpan, ekspor, dan laporan. Nilai yang sama tidak boleh diberi status berbeda antar-surface tanpa alasan/provenance yang tercatat.
6. Status tidak boleh disimpulkan dari warna saja. API dan penyimpanan harus membawa enum status eksplisit.

## 3. Aturan metrik dan bukti

### 3.1 PAR dan geometri

- PAR dapat dihitung dengan model Beer-Lambert bila umur tegakan tersedia:
  `LAI(t) = 5.5 / (1 + exp(-0.7 * (t - 3.5)))`
  `I_surface = 1800 * exp(-0.45 * LAI)`
- LAI dan PAR adalah `DETERMINISTIC_MODEL`, bukan pengukuran PAR lapangan. Cantumkan model, parameter, dan batasan profil yang digunakan.
- Untuk layout segitiga dengan jarak tanam 9 m dan radius piringan 2 m:
  `jarak antarbaris = 9 * sin(60°) ≈ 7.794 m`
  `lebar lorong model = 7.794 - 2 * 2 ≈ 3.794 m`
- Lebar lorong adalah hasil model bila jarak tanam dan buffer memang parameter kebun yang berlaku. Bila keduanya hanya asumsi standar, keluaran harus tetap `SCENARIO_PROJECTION` atau menyebut eksplisit bahwa ini geometri standar, bukan kondisi terukur blok.
- Tutupan tajuk yang berasal dari foto/vision harus dibedakan dari proxy geometri layout. Persentase hasil model tidak boleh ditampilkan sebagai persentase yang diukur AI.

### 3.2 LER, penghematan lahan, dan manfaat iklim

LER hanya dihitung jika empat input hasil panen tersedia, valid, dan menggunakan periode serta basis satuan yang sebanding:

`LER = (Y_palm_intercrop / Y_palm_monoculture) + (Y_crop_intercrop / Y_crop_monoculture)`

- Bila salah satu yield belum ada: LER, PLS, lahan terselamatkan, dan metrik turunan yield berstatus `DATA_PENDING`.
- PLS hanya bermakna sebagai penghematan relatif bila `LER > 1`; rumusnya `(1 - 1/LER) * 100%`.
- Luas pembanding yang digunakan di tampilan dan API harus konsisten. Bila memakai rumus `area * (LER - 1)`, labeli sebagai **equivalent monoculture land difference/model estimate**, bukan bukti bahwa hutan tertentu benar-benar terselamatkan.
- Perubahan area terdampak atau karbon harus dihitung dari satu definisi yang sama dan diuji terhadap komparator. Jangan menyebut suatu hasil “forest spared”, “avoided deforestation”, atau klaim kredit karbon terverifikasi tanpa metodologi, baseline, lokasi, additionality, dan verifikasi yang sesuai.
- Jika faktor `450 tCO₂e/ha` atau `1.8 tCO₂e/ha` digunakan, ungkapkan faktor, sumber, periode, dan modelnya sebagai asumsi/proyeksi. Label statusnya `SCENARIO_PROJECTION` kecuali faktor tersebut didukung metodologi proyek yang tervalidasi. Jangan mengklaim VM0007 atau kredit karbon hanya karena faktor diterapkan.
- Status EUDR/ISPO/compliance tidak dapat disimpulkan dari LER atau hasil karbon. Pemeriksaan kepatuhan harus memiliki jalur bukti dan evaluasi tersendiri.

### 3.3 Keuangan dan harga komoditas

- Tanpa kontrak offtake atau bukti harga lokal yang dapat ditelusuri, hasil harga adalah skenario; bukan harga transaksi atau pendapatan aktual.
- Parameter harga TBS dari System Control boleh dipakai untuk skenario harga TBS, dengan sumber, tanggal berlaku, satuan, dan semua komponen formula yang diperlukan. Label wajib `SCENARIO_PROJECTION`.
- Harga TBS saja tidak cukup untuk menghitung pendapatan kebun. Yield TBS aktual, basis luas/periode, serta biaya relevan tetap diperlukan.
- Jangan memakai harga/yield default katalog tanaman sela untuk menyajikan pendapatan.
- Nama kontainer yang disetujui bila skenario valuasi ditampilkan: **Simulated Economic Potential (Scenario)**.
- Disclaimer yang ditampilkan bersama hasil:
  > Berdasarkan simulasi harga pasar indikatif dan parameter skenario karbon/komoditas yang tercatat. Bukan jaminan pendapatan, harga transaksi, kredit karbon, atau kontrak offtake terverifikasi.
- Jika harga atau yield yang dibutuhkan tidak tersedia, tampilkan `DATA_PENDING`, bukan angka nol atau total manfaat finansial yang tampak final.
- Arus kas 10 tahun hanya boleh dirender sebagai proyeksi jika asumsi yield masa depan, harga, biaya, inflasi/escalation, kurs, diskonto, dan horizon tercatat. Selain itu, tampilkan alasan data pending.

### 3.4 Hidrologi, biomassa, dan bio-sirkularitas

- SCS-CN memerlukan hujan untuk periode dan lokasi yang sesuai, Hydrologic Soil Group/parameter tanah yang memiliki provenance, kondisi tutupan/penggunaan lahan, serta baseline yang dinyatakan. Tanpa data lokal tersebut, hasil hanya boleh menjadi `SCENARIO_PROJECTION`.
- Bila menggunakan baseline regional, tampilkan metodologi secara eksplisit, misalnya:
  > SCS-CN Curve Number: estimasi regional menggunakan baseline curah hujan Madina 2.188 mm/tahun dan Hydrologic Soil Group B; bukan pengukuran blok. Validasi stasiun hujan dan tanah lokal belum tersedia.
- Angka regional di atas adalah parameter skenario yang perlu pemilik data tetapkan dan verifikasi; teks ini sendiri tidak mengesahkan ketepatan ilmiah, lokasi, periode, atau nilai HSG-nya.
- Recharge dan runoff harus berasal dari implementasi water-balance yang terdokumentasi; perubahan CN saja tidak membuktikan aquifer recharge atau pengurangan limpasan.
- Bila biomassa dihitung memakai alometri Chave et al. (2014), semua input dan penerapan model harus sesuai domain metodologi. Estimasi berbasis DBH/tinggi/kepadatan hasil asumsi harus berstatus `SCENARIO_PROJECTION`, bukan `FIELD_MEASURED`.
- Catatan minimum untuk estimasi tersebut:
  > Biomassa AGB: model pantropical alometrik Chave et al. (2014); belum dikalibrasi dengan inventaris atau uji destruktif lapangan.
- Jangan menampilkan produksi pelepah, kandungan K₂O, pemulihan unsur hara, atau penghematan pupuk sebagai data aktual tanpa pengukuran biomass, analisis nutrisi, dan catatan pengembalian biomassa ke lahan.

### 3.5 Kesesuaian tanaman dan matriks komoditas

- Filter deterministik boleh memakai umur, pH, lereng, tekstur, dan spesifikasi katalog jika batasan serta sumber katalog diketahui.
- Matriks harus membedakan **kesesuaian model/katalog** dari rekomendasi agronomi terverifikasi atau hasil produksi aktual.
- Harga dan hasil katalog hanya metadata referensi/skenario. Jangan meneruskannya ke perhitungan pendapatan seolah-olah harga lokal dan yield estate.
- Jika data kebun yang dibutuhkan tidak ada, tampilkan alasan yang spesifik; jangan memakai nilai profil cadangan.

## 4. Status kartu dan tampilan

Setiap kartu atau hasil penting harus menyediakan:

- nilai dan unit, atau keadaan `DATA_PENDING` yang dapat dibaca;
- badge empat-status;
- sumber input dan waktu/provenance jika `FIELD_MEASURED`;
- nama rumus/versi serta input efektif jika `DETERMINISTIC_MODEL`;
- asumsi, parameter yang dapat diubah, sumber/tanggal, dan disclaimer jika `SCENARIO_PROJECTION`;
- daftar input wajib yang hilang jika `DATA_PENDING`.

Hindari indikator seolah-olah semua ambang sudah lulus, status “verified”, “compliant”, “sealed”, atau angka default di placeholder HTML. Nilai hasil kalkulasi harus mengganti placeholder hanya setelah respons berhasil divalidasi. Kegagalan API tidak boleh membuat UI menampilkan sukses, angka lama, atau hasil fallback yang menyamar sebagai hasil engine.

## 5. Transaksi dossier dan Strict Transactional Sealing

Segel audit hanya boleh diterbitkan oleh backend setelah validasi dan commit permanen berhasil. Rincian normatif dan skema request/response berada di [kontrak_api_simulator_sealing.md](./kontrak_api_simulator_sealing.md).

Aturan UI:

1. Status `SEALED & COMMITTED TO LEDGER #REC-...` hanya muncul setelah respons backend sukses, berisi record ID, hash server, dan pengakuan commit.
2. Pada kegagalan, offline, timeout, atau respons yang tidak valid, jangan membuat ID/hash pengganti dan jangan mengunci input.
3. Tampilkan status `UNCOMMITTED / LOCAL DRAFT ONLY • PENDING SERVER PERSISTENCE`. Draft lokal—jika fitur itu ada—harus jelas berbeda dari record ledger dan tidak boleh memiliki badge segel.
4. Timeout atau koneksi terputus setelah pengiriman menciptakan **hasil commit yang belum diketahui**: pertahankan draft, tampilkan status pending, lalu rekonsiliasi menggunakan idempotency key. Jangan menebak gagal atau berhasil.
5. Setelah rekonsiliasi memastikan record telah committed, barulah UI dapat memulihkan status sealed. Jika backend menyatakan tidak ada record untuk key itu, pengguna dapat mencoba commit ulang dengan key yang sama.
6. Form hanya boleh terkunci untuk dossier yang benar-benar committed, dan harus mengikuti kontrol unlock/recalibration yang eksplisit. UI membuka kunci kembali bila commit gagal; timeout/hasil tidak diketahui mempertahankan pending state dan key yang sama.

SQLite dan BigQuery tidak menyediakan satu transaksi atomik lintas layanan secara umum. Jika SQLite menjadi ledger otoritatif lokal, status commit lokal dan status sinkronisasi BigQuery harus menjadi dua status terpisah. Jangan menyebut “BigQuery committed” sampai konfirmasi sinkronisasi BigQuery diterima. Strategi ledger otoritatif cloud harus ditentukan sebelum deployment yang menjanjikan commit cloud.

## 6. Kontrak kalkulasi

- Backend `kalkulasi.engine` adalah produsen angka kanonis untuk endpoint kalkulasi Simulator; model iklim didelegasikan ke `kalkulasi.ekonomi_karbon` melalui wrapper engine.
- Preview kalkulasi boleh menerima input parsial untuk menampilkan metrik yang tidak bergantung pada yield. Respons harus mempertahankan `DATA_PENDING` pada metrik yang membutuhkan yield.
- Endpoint penyimpanan audit tidak boleh menerima angka kalkulasi dari browser sebagai kebenaran. Backend harus memvalidasi input, memuat profil berwenang, menghitung ulang, lalu menyimpan snapshot input/output dan status.
- Data lama/record historis tidak boleh dipakai sebagai fallback untuk perhitungan estate aktif tanpa keterkaitan record, estate, dan versi kalkulasi yang eksplisit.
- Versi rumus/engine, identitas/profil estate, waktu commit UTC, input/output, status metrik, bukti yang dirujuk, asumsi, dan idempotency key tersedia di snapshot audit. Bukti input yield masih ditandai pending provenance.
- AI boleh dijalankan setelah atau paralel dengan kalkulasi deterministik. Kegagalan/quota AI tidak menghapus atau mengganti hasil engine; fallback AI harus dilabeli terpisah.

## 7. Checklist acceptance untuk spesifikasi

- [ ] Semua nilai UI/API/dossier menggunakan enum status empat kategori yang konsisten.
- [x] PAR pada umur 7,5 tahun mengikuti rumus dan parameter engine yang disepakati, diberi label `DETERMINISTIC_MODEL`; bukan `FIELD_MEASURED` (uji preview).
- [ ] Lebar lorong 3,79 m diberi label sesuai provenance jarak tanam/buffer; bukan otomatis terukur.
- [ ] Tanpa empat yield, LER/PLS/manfaat lahan yield-dependent berstatus `DATA_PENDING`, tidak memakai default.
- [ ] Dengan yield lengkap, LER dan PLS konsisten dengan rumus serta unit/periode input yang sebanding.
- [x] Faktor karbon 450 dan soil-carbon 1,8 dijelaskan sebagai faktor skenario; tidak menyatakan kredit karbon atau kepatuhan.
- [ ] Harga TBS dari System Control ditandai scenario; pendapatan tidak ada tanpa yield dan biaya relevan.
- [ ] Matriks tanaman tidak mengubah harga/yield katalog menjadi nilai estate.
- [ ] Angka recharge, CN, biomass, microclimate, frond, atau K₂O tidak tersaji sebagai measured tanpa bukti yang sesuai.
- [ ] Simulasi finansial memiliki disclaimer dan bukan label “Total Economic Benefit” yang tidak berkualifikasi.
- [x] API hanya memberikan segel setelah persistensi SQLite otoritatif sukses.
- [x] Retry/response loss dapat direkonsiliasi menggunakan idempotency key tanpa duplicate record atau false seal (uji transaction/replay/conflict).
- [x] Status ledger lokal dan sinkronisasi cloud dibedakan; BigQuery saat ini `NOT_CONFIGURED`.
- [ ] Kegagalan AI atau cuaca tidak menghapus output deterministik dan tidak memalsukan telemetry.

## 8. Keputusan sebelum deployment non-lokal

1. Implementasi lokal memakai SQLite sebagai ledger otoritatif. Tentukan ledger cloud sebelum mengiklankan komit lintas perangkat.
2. Tambahkan autentikasi, otorisasi estate/tenant, dan audit akses sebelum endpoint tersedia di jaringan publik.
3. Parameter mana yang boleh menjadi skenario regional (misalnya curah hujan, HSG, faktor karbon), siapa pemiliknya, dan bagaimana versi/tanggal berlakunya?
4. Bukti minimum apa yang mengangkat setiap field ke `FIELD_MEASURED`? Endpoint v1 belum menerima/menilai evidence provenance yield.
5. Formula/faktor karbon dan biofisika mana yang sudah disetujui sebagai model internal, dan mana yang hanya ilustrasi?

Sampai keputusan tersebut disetujui, ketentuan yang lebih konservatif berlaku: tampilkan `DATA_PENDING` atau `SCENARIO_PROJECTION`; jangan menerbitkan klaim ukur, finansial, kepatuhan, atau segel yang belum dibuktikan.
