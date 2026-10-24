# Kontrak API Simulator: Validasi, Persistensi, dan Segel

**Status:** kontrak implementasi lokal v1; autentikasi/provenance masih menjadi batasan sebelum deployment publik  
**Endpoint sasaran:** `POST /api/simulate`  
**Ruang lingkup:** membuat dossier simulasi yang dapat ditelusuri dan mencegah false seal.

## 1. Invariants kontrak

1. Backend adalah otoritas untuk validasi profil, kalkulasi, record ID, timestamp, status commit, dan hash.
2. Browser tidak dapat meminta atau memaksa record berstatus `SEALED` melalui field request.
3. Hash bukan bukti persistensi. Hash/record ID yang dikembalikan sebagai bukti committed hanya diterbitkan setelah commit ke ledger otoritatif berhasil.
4. Input panen yang dibutuhkan oleh metrik yield-dependent harus tersedia, numerik, positif, memiliki satuan/periode yang sebanding, dan terkait dengan estate yang diizinkan.
5. Hasil kalkulasi dikomputasi ulang di backend. Field hasil numerik yang dikirim klien, jika diterima untuk kompatibilitas, tidak menjadi sumber kebenaran dan tidak boleh mengalahkan output backend.
6. Semua nilai metrik memiliki status `FIELD_MEASURED`, `DETERMINISTIC_MODEL`, `SCENARIO_PROJECTION`, atau `DATA_PENDING`, beserta provenance yang relevan.
7. Request yang sama dengan idempotency key yang sama tidak boleh membuat record committed duplikat.

### Implementasi lokal v1 yang tersedia

- `POST /api/simulate` menerima field kompatibilitas saat ini (`kode_kebun`, `palm_age`/`palm_age_years`, `land_area`/`land_area_ha`, `crop_name`, empat input yield, dan parameter profil). Kode estate, umur, dan luas harus eksplisit; seluruh input yield harus lengkap untuk menyimpan LER.
- Record disimpan di `compute_audit_logs`; `idempotency_key`, `idempotency_payload_hash`, dan `canonical_snapshot_json` ditambahkan melalui migrasi aditif.
- Key wajib 16–128 karakter aman. Fingerprint payload dibuat backend. Key sama + fingerprint sama mengembalikan record lama; key sama + payload berbeda menghasilkan `409`.
- Commit baru mengembalikan `201`; replay committed `200`; validasi gagal memakai `4xx`; error transaksi yang hasilnya tidak dapat dipastikan mengembalikan `500 COMMIT_STATUS_UNKNOWN`.
- `GET /api/simulate/commit-status` memakai key yang sama dan mengembalikan snapshot jika committed. `cloud_sync.status` saat ini `NOT_CONFIGURED` kecuali status sinkronisasi SQLite membuktikan `SYNCED`.
- Yield yang dikirim pengguna belum memiliki provenance tervalidasi sehingga input berstatus `SCENARIO_PROJECTION`, bukan `FIELD_MEASURED`. Foto/Vision summary klien disimpan sebagai referensi tidak terverifikasi.
- Belum ada autentikasi/otorisasi tenant/estate pada endpoint ini. Idempotency key berentropi tinggi hanya berfungsi sebagai capability untuk pemakaian lokal, bukan pengganti autentikasi. Jangan publikasikan endpoint sebelum kontrol akses ditambahkan.
- Tombol pasca-commit membuka dossier lokal; endpoint sertifikat BigQuery tidak ditautkan sampai sinkronisasi record terkonfirmasi.

## 2. Header dan idempotensi

Request wajib membawa:

```http
Content-Type: application/json
Idempotency-Key: <random UUID generated once for this save attempt>
```

- Key dibuat sekali untuk satu upaya simpan dan disimpan pada draft browser hingga hasil commit diketahui.
- Retry setelah timeout memakai key yang sama. Key berbeda berarti niat pembuatan record baru.
- Backend menyimpan key dengan constraint unik dan mengikatnya pada fingerprint payload request yang dikanonicalisasi. Identitas pemohon/tenant belum tersedia pada implementasi lokal v1.
- Bila key yang sama datang dengan payload berbeda, backend mengembalikan `409 IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_PAYLOAD`.
- Pengungkapan ulang record melalui key wajib melewati otorisasi yang sama seperti pembacaan record biasa saat autentikasi diterapkan. V1 dibatasi untuk penggunaan lokal tepercaya.

## 3. Request schema

Contoh berikut adalah kontrak konseptual; field identitas user/tenant dapat ditetapkan oleh autentikasi server dan tidak perlu dipercaya dari body.

```json
{
  "schema_version": "simulator.save.v1",
  "kode_kebun": "EST-MDN-010",
  "calculation_inputs": {
    "palm_age_years": 10.0,
    "land_area_ha": 50.0,
    "crop_name": "Red Ginger",
    "yield_palm_inter_t_ha_period": 20.0,
    "yield_palm_mono_t_ha_period": 22.0,
    "yield_crop_inter_t_ha_period": 6.0,
    "yield_crop_mono_t_ha_period": 12.0,
    "soil_ph": 5.2,
    "slope_degrees": 4.5,
    "elevation_m_asl": 220.0,
    "soil_texture": "clay"
  },
  "input_provenance": {
    "yield_palm_inter_t_ha_period": {
      "status": "FIELD_MEASURED",
      "source_type": "PKS_WEIGHBRIDGE_TICKET",
      "source_reference": "ticket-reference",
      "observed_at": "2026-10-24T00:00:00Z",
      "period_start": "2026-10-01",
      "period_end": "2026-10-24",
      "unit": "t/ha/period"
    }
  },
  "scenario_parameters": {
    "tbs_pricing_configuration_version": null,
    "carbon_factor_tco2e_ha": null,
    "regional_rainfall_mm_year": null,
    "hydrologic_soil_group": null
  },
  "evidence": {
    "photo_evidence_ids": [],
    "vision_result_ids": []
  },
  "ai_reasoning_reference": null
}
```

### Validation rules

- `schema_version`, `kode_kebun`, `calculation_inputs`, dan idempotency key wajib.
- Estate harus ditemukan dan caller harus berhak mengakses estate tersebut.
- Area harus positif dan tidak melampaui batas area yang terdaftar, kecuali ada kewenangan serta alasan perubahan yang terekam.
- Umur, pH, lereng, elevasi, tekstur, dan koordinat harus mengikuti rentang/unit yang disepakati. Field yang tidak dapat divalidasi tidak boleh diam-diam diganti nilai default.
- Nilai yield untuk membuat dossier LER wajib lengkap; setiap nilai harus lebih besar dari nol, mempunyai satuan/periode, dan basis area yang konsisten.
- Referensi yield UI memakai database alias crop-key dan model logistik umur sawit (versi 2), dengan asumsi yield monokultur maksimum 26,5 t/ha, laju 0,65, titik tengah umur 3,5 tahun, dan penalti antar-tanam per komoditas. Ini bukan model Chapman-Richards atau Beer-Lambert. Seluruh nilai hanya `SCENARIO_PROJECTION`, bukan data terukur atau rekomendasi tervalidasi.
- Database mencakup 15 komoditas katalog awal dan tambahan Shade Cacao, total 16 pilihan, termasuk alias nama umum, nama Indonesia, dan nama ilmiah. Enam komoditas tanpa benchmark khusus memakai nilai generik/komoditas pembanding yang tetap diberi label asumsi; nama yang tidak dikenali memakai fallback generik. Backend menghitung ulang nilai untuk model, umur, dan crop-key yang dinyatakan; nilai yang tidak cocok ditandai `USER_PROVIDED_UNVERIFIED`.
- Jika yield tidak lengkap, endpoint penyimpanan menolak pembuatan dossier LER/karbon dengan `422 DATA_PENDING`. Preview parsial adalah tanggung jawab endpoint preview terpisah dan tidak menerbitkan segel.
- Provenance tidak dapat menyatakan `FIELD_MEASURED` hanya dengan mengirim string status. Backend memvalidasi jenis sumber/rujukan sesuai kebijakan evidence dan menyimpan hasil pemeriksaan provenance.
- Parameter skenario harus menyertakan versi, sumber, tanggal berlaku, unit, dan disclaimer yang diwajibkan sebelum digunakan.
- `carbon_price_usd` pada System Control adalah harga skenario yang dapat dikonfigurasi, bukan harga pasar terverifikasi atau kontrak offtake. Nilai karbon yang dihitung dari parameter ini harus berstatus `SCENARIO_PROJECTION`; pendapatan tanaman sela tetap kosong tanpa harga dan biaya terverifikasi.
- Preview biofisika yang memakai asumsi regional wajib menyimpan catatan metode dan berstatus `SCENARIO_PROJECTION`: biomassa usia-saja bukan persamaan Chave et al. (2014) atau inventaris lapangan; pendinginan mengasumsikan tutupan tanaman sela 65%; dan SCS-CN memakai baseline regional Madina 2.188 mm/tahun serta HSG B. Keluaran limpasan bukan pengukuran recharge akuifer.
- Output bio-circularity saat ini adalah ilustrasi berbasis asumsi regional 10,8 ton bahan kering pelepah/ha/tahun dan rasio nutrien asumsi. Output K₂O/N tidak membuktikan biomassa, kandungan laboratorium, pengembalian pelepah ke lahan, atau penghematan pupuk terukur; statusnya `SCENARIO_PROJECTION`.
- Proyeksi 10 tahun pada UI hanya gross inflow skenario: harga TBS dari System Control dan harga tanaman sela katalog, dikombinasikan dengan yield input/model. Ini bukan pendapatan terealisasi; biaya operasi, valuasi kredit karbon, payback, dan NPV bersih tidak dihitung tanpa sumber/kontrak biaya yang memadai. Tingkat diskonto 10% adalah asumsi tampilan untuk present value gross inflow, bukan WACC terverifikasi.
- Lebar koridor 3,79 m hanya deterministik untuk pola segitiga 9 m dan buffer akar 2 m yang dimodelkan. Tanpa survei tata letak blok, hasil tidak boleh disebut pengukuran lapangan.
- Foto atau hasil Vision AI hanya dikaitkan melalui ID evidence yang berwenang; path bebas dari klien tidak menjadi bukti tersimpan.
- `ai_reasoning_reference` bersifat non-authoritative terhadap angka kalkulasi dan status commit.

## 4. Urutan operasi backend yang diwajibkan

1. Sebelum deployment non-lokal, autentikasi, otorisasi estate, dan validasi evidence wajib diterapkan. V1 lokal memvalidasi schema dan key, tetapi belum menyediakan kontrol akses.
2. Periksa mapping idempotensi unik di `compute_audit_logs`. Jika key sudah berhasil diproses dengan payload sama, kembalikan hasil committed yang sama; jangan membuat record baru.
3. Validasi unit, periode, batas nilai, kelengkapan yield dan provenance; kumpulkan kesalahan per field.
4. Muat profil terkini yang authorized dari ledger/profil utama. Jangan memakai profil atau harga dari payload klien untuk menimpa sumber authoritative tanpa aturan update yang tercatat.
5. Jalankan kalkulasi engine versi yang dicatat. Hitung status output dan status dependency secara eksplisit.
6. Bentuk snapshot canonical yang mencakup ID record, estate/profil, input efektif, status input/output, asumsi skenario, versi engine/schema, evidence references, waktu UTC, dan idempotency key. V1 menandai provenance input yield sebagai belum diverifikasi.
7. Dalam transaksi SQLite `BEGIN IMMEDIATE`: simpan record, snapshot dan mapping idempotensi, lalu hash SHA-256 dari representasi canonical. Jika salah satu gagal, rollback semuanya.
8. Kembalikan status committed hanya setelah database mengonfirmasi commit.
9. Sinkronisasi BigQuery/cloud diproses sesuai strategi yang dipilih. Jika sinkronisasi tidak merupakan bagian dari ledger transaksional yang sama, catat status sinkronisasi terpisah dan jangan menyebutnya sebagai commit atomik.

### Canonical hash

- Algoritme hash: SHA-256.
- V1 memakai JSON dengan key terurut (`sort_keys`), separator `,` dan `:` tanpa spasi, UTF-8, `ensure_ascii=False`, dan timestamp UTC ISO-8601 berakhiran `Z`. Representasi yang sama disimpan pada `canonical_snapshot_json` dan menjadi byte input SHA-256 (digest uppercase).
- Perubahan aturan canonicalization memerlukan versi schema/hash baru.
- Hash tidak memuat nilai yang tidak ikut disimpan atau yang masih dapat berubah tanpa versi baru.
- Hash tidak menggantikan autentikasi, otorisasi, immutable log, backup, maupun pemeriksaan integritas ledger.
- Hash foto dan hash snapshot dossier adalah konsep berbeda; keduanya harus mempunyai field, sumber byte, dan tujuan yang jelas.

## 5. Respons

### 5.1 Commit sukses

`201 Created` untuk commit baru, atau `200 OK` untuk pengembalian hasil idempotent yang sudah committed:

```json
{
  "success": true,
  "commit_status": "COMMITTED",
  "ledger": {
    "authority": "LOCAL_SQLITE",
    "record_id": 123,
    "committed_at": "2026-10-24T16:08:37Z",
    "sha256": "server-generated-64-character-hex-digest",
    "idempotency_key": "request-key"
  },
  "cloud_sync": {
    "status": "NOT_CONFIGURED",
    "target": "BIGQUERY"
  },
  "calculation_engine": "kalkulasi.engine",
  "engine_version": "kalkulasi.engine-v1",
  "data_numerik": {},
  "metric_statuses": {
    "ler": "DETERMINISTIC_MODEL",
    "yield_inputs": "SCENARIO_PROJECTION"
  }
}
```

- `ledger.authority` wajib mengidentifikasi ledger yang commit-nya terbukti.
- `cloud_sync.status` tidak boleh disimpulkan dari commit lokal; gunakan status seperti `PENDING`, `SYNCED`, `FAILED`, atau `NOT_CONFIGURED` berdasarkan bukti sinkronisasi.
- `201` hanya untuk record baru. Retry yang menemukan record sukses sebelumnya tidak membuat record kedua.

### 5.2 Validasi gagal

Gunakan kode `4xx`, tanpa `record_id`, tanpa hash yang tampak sebagai segel, dan tanpa `commit_status: COMMITTED`.

```json
{
  "success": false,
  "commit_status": "NOT_COMMITTED",
  "error": {
    "code": "DATA_PENDING",
    "message": "Measured yield data is required before a LER dossier can be committed.",
    "fields": [
      "yield_palm_inter_t_ha_period",
      "yield_palm_mono_t_ha_period"
    ]
  }
}
```

### 5.3 Backend tidak tersedia atau kegagalan commit

- `5xx`/gateway error tidak boleh membawa sukses semu, record ID placeholder, timestamp commit, atau hash hasil klien.
- Bila backend mengetahui transaksi rollback, nyatakan `NOT_COMMITTED`.
- Bila backend tidak dapat memastikan hasil transaksi, nyatakan `COMMIT_STATUS_UNKNOWN` hanya pada jalur yang sesuai; klien harus merekonsiliasi dengan idempotency key.

## 6. Rekonsiliasi status commit

V1 menyediakan mekanisme lokal untuk memeriksa satu idempotency key, misalnya:

```http
GET /api/simulate/commit-status
Idempotency-Key: <same key>
```

Key acak berentropi tinggi diperlakukan sebagai capability lokal. Ini bukan autentikasi yang memadai untuk layanan publik. Sebelum deployment, lookup wajib mendapat scope identity/tenant dan otorisasi yang sama dengan read record biasa.

Respons hanya salah satu dari:

- `COMMITTED`: kembalikan record ID, hash, commit timestamp, snapshot, dan status sinkronisasi yang aktual.
- `NOT_COMMITTED`: key belum memiliki record commit; klien dapat menawarkan retry dengan key yang sama.
- `PROCESSING` atau `UNKNOWN`: rekonsiliasi belum selesai; pertahankan state draft/pending dan jangan kunci form.

Endpoint lookup tidak boleh mengungkap keberadaan record tenant/estate yang tidak diotorisasi.

## 7. Perilaku klien/UI

| Kondisi | Label yang boleh ditampilkan | Input | Tindakan |
|---|---|---|---|
| Respons commit terverifikasi | `SEALED & COMMITTED TO LEDGER #REC-...` | Boleh dikunci sesuai kebijakan dossier | Tampilkan hash server dan ledger authority. |
| Validasi gagal | `NOT COMMITTED • DATA PENDING` | Tetap dapat diperbaiki | Tampilkan field dan pesan yang gagal. |
| Offline/timeout/response loss | `UNCOMMITTED / LOCAL DRAFT ONLY • PENDING SERVER PERSISTENCE` | Jangan dikunci | Simpan draft/key bila diaktifkan, rekonsiliasi sebelum retry. |
| Commit lokal terkonfirmasi, cloud belum tersinkron | `COMMITTED TO LOCAL LEDGER • CLOUD SYNC PENDING` | Mengikuti kebijakan ledger | Jangan klaim BigQuery/cloud committed. |
| Sinkronisasi cloud terkonfirmasi | `COMMITTED • CLOUD SYNCED` hanya jika sesuai arsitektur | Mengikuti kebijakan ledger | Simpan bukti ack/status sinkronisasi. |

UI dilarang:

- membuat `Date.now()` ID, hash statis, hash acak, atau digest client sebagai bukti committed;
- mengubah exception/timeout menjadi hasil sukses atau fallback “local SQLite mode active” tanpa commit lokal yang benar-benar terbukti;
- mengunci form atau menampilkan seal sebelum commit sukses;
- menghapus draft atau mengganti idempotency key sebelum status request sebelumnya diketahui;
- menganggap HTTP sukses tanpa memvalidasi schema respons, `commit_status`, dan metadata ledger.

## 8. Kebijakan ekspor dan pembacaan record

- Ekspor record harus mengambil snapshot committed yang sama; jangan membentuk ulang isi dossier dari state DOM yang dapat berubah.
- Nilai scenario dan pending harus diserialisasi bersama status, asumsi, unit, dan provenance-nya.
- Record lama yang tidak memiliki provenance/status baru harus dipetakan sebagai `DATA_PENDING` atau status legacy yang eksplisit, bukan dinaikkan otomatis ke `FIELD_MEASURED`.
- Endpoint GET mengembalikan hash serta metadata committed yang berasal dari ledger. Ia tidak boleh menghitung hash baru lalu menyajikannya seolah-olah hash tersebut menyegel konten lama.

## 9. Hal yang masih memerlukan keputusan arsitektur

Sebelum kontrak diberlakukan, pemilik sistem harus menetapkan:

1. Ledger otoritatif per mode non-lokal dan definisi “permanen”.
2. Apakah BigQuery adalah ledger, read replica/warehouse, atau target sinkronisasi. V1 lokal belum mengantrekan sinkronisasi.
3. Perilaku ketika commit SQLite berhasil tetapi sinkronisasi BigQuery gagal.
4. Auth/tenant scoping wajib ditambahkan sebelum expose endpoint; tetapkan juga retensi, audit akses, backup, dan mekanisme koreksi/versioning record immutable.
5. Kebijakan verifikasi provenance untuk kartu timbang, AWS, GPS, pengukuran tanah, dan evidence Vision.
6. Batas waktu/retensi idempotency key dan mekanisme rekonsiliasi setelah restart server.
7. Versi algoritme canonicalization/hash dan pengelolaan perubahan schema.

Kontrak ini tidak menyatakan bahwa transaksi lintas SQLite dan BigQuery bersifat atomik. Jika dibutuhkan status cloud committed, diperlukan ledger cloud otoritatif atau protokol konsensus/acknowledgement yang eksplisit, bukan sekadar dual-write best effort.
