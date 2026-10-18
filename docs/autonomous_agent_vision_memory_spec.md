# Spesifikasi Arsitektur Sistem: Autonomous Learning Agent & Dynamic Spatial Multi-Object Vision

**Status Dokumen:** Konsensus Arsitektur Disepakati  
**Sistem:** Precision Palm — Biophysical Agroforestry Intelligence  
**Komponen:** Multimodal Vision Scanner (4D) + Episodic Memory RAG + Self-Evolving Experience Loop  

---

## 1. Ringkasan Konsensus: Menghapus Mockup Statis & Membangun Visi Cerdas Nyata

### 1.1 Masalah Sistem Lama (Yang Dihapus Total)
* Koordinat persentase kotak statis (*hardcoded bounding box*) yang menggantung sembarangan di atas foto parit, semak belukar, maupun foto udara drone.
* AI kaku yang bekerja secara *stateless* (sekali panggil selesai, lupa riwayat sebelumnya, mengulangi halusinasi yang sama).

### 1.2 Pilar Kekuatan Baru yang Disepakati
1. **Deteksi Objek Fisik Nyata (Multi-Object HUD 15–25 Entitas):**
   * *Perspektif Udara (Drone Nadir $Z > 15\text{ m}$):* Menghitung pohon sawit individual (*Tree Counting* #1..#N), mendeteksi jalan kebun (*Haul Road*), memetakan parit drainase (*Canal*), dan mengidentifikasi pola tanam kontur vs segitiga sama sisi.
   * *Perspektif Darat (Mandor In-Situ $Z \le 2\text{ m}$):* Mendeteksi batang sawit kiri & kanan, tandan buah segar (TBS matang/mentah), piringan tanah bersih (*weed-free circle*), tumpukan pelepah pangkasan (*frond mulch pile*), dan permukaan lorong gawangan terbuka.
2. **Kalkulus Lahir dari Jarak Benda Nyata:**
   * Lebar lorong bersih $3{,}79\text{ m}$ bukan kotak fiktif, melainkan hasil perhitungan jarak antara *Batang Pokok Kiri* dan *Batang Pokok Kanan* dikurangi radius piringan steril $2 \times 2{,}0\text{ m}$.
3. **Agen Mandiri Berbasis Episodic RAG (Self-Evolving Memory Loop):**
   * Setiap hasil pemindaian dan verifikasi lapangan disimpan ke dalam basis memori jangka panjang (*Long-Term Memory Ledger* di SQLite WAL & BigQuery DW).
   * Agen AI membaca memori audit blok sebelum menganalisis foto baru, membandingkan laju pertumbuhan temporal, dan mencegah pengulangan kesalahan tanpa harus meminta pengguna memasukkan data dari nol.

---

## 2. Taksonomi 20+ Objek Fisik Nyata & Filter Layer HUD

### 2.1 Mode Aerial Drone (Ketinggian $Z > 15\text{ m}$)
| Klaster | Objek Fisik Nyata | Warna & Label HUD | Signifikansi Matematis / Agronomi |
| :--- | :--- | :--- | :--- |
| **Pohon Sawit** | Individual Palm Crown #01..#25 | `emerald` `[🌴 Palm Tree #N]` | Menghitung populasi tegakan riil per hektar (Target 136–143 pokok/Ha). |
| **Infrastruktur** | Main Haul Road (6.0m) / Parit | `amber` `[🚜 Haul Road]` / `cyan` `[💧 Canal]` | Memisahkan zona transportasi dan hidrologi dari area budidaya tanaman sela. |
| **Pola Lahan** | Contour Terrace / Open Gap | `purple` `[🌀 Contour Line]` / `rose` `[⚠️ Missing Stand]` | Memverifikasi kelerengan teras kontur dan titik sisipan pohon mati. |

### 2.2 Mode Terrestrial Mandor (Ketinggian $Z \le 2\text{ m}$)
| Klaster | Objek Fisik Nyata | Warna & Label HUD | Signifikansi Matematis / Agronomi |
| :--- | :--- | :--- | :--- |
| **Anatomi Pokok** | Trunk Pokok Kiri & Pokok Kanan | `emerald` `[🌴 Palm Trunk A/B]` | Mengunci titik dasar pengukuran lebar koridor gawangan ($W_{\text{corridor}}$). |
| **Organ Buah** | Tandan Buah Segar Masak / Mentah | `amber` `[🍇 FFB Ripe / Mature]` | Memvalidasi fase fisiologis Tanaman Menghasilkan (TM) dan potensi tonase. |
| **Zona Piringan** | Piringan Tanah Lingkaran Batang | `rose` `[⭕ Clean Root Buffer Circle]` | Memverifikasi radius $2{,}0\text{ m}$ steril tanpa cangkulan mekanis (*zero-tillage*). |
| **Lantai Gawangan**| Serasah Pelepah / Lorong Aktif | `teal` `[🍂 Pruned Frond Mulch]` | Memvalidasi siklus hara pelepah ($+36{,}2\text{ kg K}_2\text{O/Ha}$) dan ruang tanam sela $3{,}79\text{ m}$. |

---

## 3. Desain Agen AI Mandiri: Arsitektur Episodic Memory RAG

Agen tidak bekerja secara instan tanpa ingatan. Agen dibekali siklus pembelajaran adaptif 4 tahap:

```
    ┌────────────────────────────────────────────────────────┐
    │ 1. PENGAMBILAN MEMORI BLOK (EPISODIC RAG RETRIEVAL)   │
    │    • Membaca riwayat audit blok sebelumnya (Q1, Q2)    │
    │    • Membaca jenis komoditas terdaftar (misal: Jahe)   │
    │    • Mengambil data baseline satelit GEE (NDVI, NDMI)  │
    └───────────────────────────┬────────────────────────────┘
                                │
                                ▼
    ┌────────────────────────────────────────────────────────┐
    │ 2. INFERENSI VISI DENGAN ANCHOR MEMORI (GEMINI VISION) │
    │    • Menyesuaikan deteksi dengan ekspektasi fenologi   │
    │    • Mendeteksi objek fisik riil (20+ entitas)         │
    │    • Menilai anomali / deviasi terhadap memori blok    │
    └───────────────────────────┬────────────────────────────┘
                                │
                                ▼
    ┌────────────────────────────────────────────────────────┐
    │ 3. ANALISIS EKSPERIMENTAL & FORMULASI BIOFISIKA       │
    │    • Membandingkan pertumbuhan tanaman aktual vs target │
    │    • Menyesuaikan dosis pupuk MOP & rekomendasi tanah  │
    │    • Menerbitkan status kepatuhan (Discrepancy Check)  │
    └───────────────────────────┬────────────────────────────┘
                                │
                                ▼
    ┌────────────────────────────────────────────────────────┐
    │ 4. PENYIMPANAN PENGALAMAN BARU (MEMORY UPDATE LOOP)    │
    │    • Menulis hasil audit ke tabel `agent_experience`   │
    │    • Memperbarui model vector context untuk audit Q+1  │
    │    • Mengunci segel kriptografis FIPS SHA-256          │
    └────────────────────────────────────────────────────────┘
```

### 3.1 Skema Tabel Memori Pengalaman Agen (`agent_experience`)
Setiap kali scanning selesai, agen menyegel data ke dalam basis data terstruktur:
* `block_id`: Identifikasi petak kebun (misal: `EST-MDN-001-BLOK-A`).
* `session_context`: Mode perspektif (Aerial vs Terrestrial), ketinggian AGL, dan orientasi sudut.
* `detected_entities`: Array JSON berisi 15–25 koordinat kotak fisik riil (bukan persentase statis).
* `learned_biophysical_state`: Estimasi umur, SPAD klorofil, indeks Ganoderma, dan lebar gawangan.
* `discrepancy_insights`: Catatan deviasi terhadap deklarasi sebelumnya (misal: terdaftar jagung tetapi teramati jahe).
* `experience_vector_summary`: Ringkasan teks kontekstual untuk disuntikkan ke prompt RAG pada audit berikutnya.

---

## 4. Matriks 44 Variabel Sistem: Referensi Baku

```
[ KLASTER 1: GEOSPASIAL 4D & TOPOGRAFI ]
Var 01: Longitude WGS84 (6 desimal)
Var 02: Latitude WGS84 (6 desimal)
Var 03: Altitude AGL Sensor (Ketinggian di atas tanah, meter)
Var 04: Timestamp ISO 8601 (Stempel waktu satelit terverifikasi)
Var 05: Camera Pitch Angle (Derajat kemiringan lensa)
Var 06: Ground Elevation ASL (SRTM 30m DEM)
Var 07: Micro-Terrain Slope (Kemiringan kontur, <= 15.0 derajat)
Var 08: Distance to Moratorium (Jarak ke batas PIPPIB 2024, >= 50m)

[ KLASTER 2: PENGENALAN KOMODITAS & MORFOLOGI LORONG ]
Var 09: Companion Inferred Taxon (Nama botani tanaman sela teramati)
Var 10: Declared vs Observed Discrepancy Score (Skor deviasi izin 0.0 - 1.0)
Var 11: Companion Canopy Height (Tinggi kanopi sela, cm)
Var 12: Phenology Growth Stage (Fase vegetatif / generatif)
Var 13: Foliar Aspect Ratio (Rasio panjang-lebar helai daun sela)
Var 14: Bedding Ridge Width (Lebar guludan bedengan tanah gembur, cm)
Var 15: Ground Cover Fraction (Persentase tutupan tanah sela, %)
Var 16: Noxious Weed Encroachment (Tingkat kontaminasi gulma liar, %)

[ KLASTER 3: FISIOLOGI SAWIT & PROTEKSI GANODERMA ]
Var 17: Feeder Root Radial Clearance (Radius piringan steril, >= 2.0m)
Var 18: Tillage Violation Flag (Deteksi luka cangkul di piringan akar)
Var 19: Estimated Stand Age (Umur fisiologis sawit, tahun)
Var 20: Canopy Leaf Area Index (LAI sigmoid logistik 0.0 - 5.5)
Var 21: PAR Light Transmission (Transmisi radiasi Monsi-Saeki, %)
Var 22: Foliar Chlorophyll SPAD (Kadar klorofil pelepah daun)
Var 23: Nitrogen-Potassium Vector (Status defisiensi hara N vs K)
Var 24: Ganoderma Necrosis Probability (Probabilitas busuk pangkal batang, %)

[ KLASTER 4: HIDROLOGI, NERACA HARA & KARBON ]
Var 25: Riparian Water Proximity (Jarak ke tepi badan air / parit, meter)
Var 26: Water Turbidity Index (Kekeruhan air limpasan, NTU)
Var 27: USDA Curve Number Post (Penurunan CN dari 82 ke 64)
Var 28: Aquifer Water Recharge (Volume resapan air tanah, m3/Ha/thn)
Var 29: Compensatory MOP Requirement (Pupuk penyeimbang Kalium, +kg MOP/Ha)
Var 30: Biological N-Fixation Credit (Penghematan pupuk Urea, +kg Urea/Ha)
Var 31: Land Equivalent Ratio (LER biologis, target >= 1.40x)
Var 32: Cryptographic SHA-256 Digest (Segel FIPS 180-4 tamper-proof)

[ KLASTER 5: GENETIKA PPKS, POLINASI & KASTRASI ]
Var 33: Genetic Variety Pedigree (DxP 540 NG / DxP 239 / Yangambi)
Var 34: Pollinator Beetle Density (Elaeidobius kamerunicus per Ha)
Var 35: Male Inflorescence Retention (Retensi bunga jantan mekar)
Var 36: Fruit Set Percentage (Persentase pembentukan buah jadi, > 75%)
Var 37: Castration Sanitation Status (Ablasi bunga betina TBM 12-24 bulan)

[ KLASTER 6: LSU PELEPAH-17, ETc & ISPO PERMENTAN 33/2025 ]
Var 38: LSU Frond-17 Phyllotaxis (Verifikasi sampel pelepah ke-17)
Var 39: Critical Leaf Nutrient Matrix (% N > 2.75, % K > 1.25, % Mg > 0.25)
Var 40: Micronutrient Vector (Skrining Little Leaf / defisiensi Boron, Cu, Zn)
Var 41: Crop Evapotranspiration Rate (ETc = 0.93 x ETo, mm/tahun)
Var 42: Peatland Water Table (Muka air gambut sekat kanal, > -40cm)
Var 43: Circular Mulch Recycling (Aplikasi TKKS 20-40 t/Ha & Abu Boiler)
Var 44: ISPO Mass Balance Tier (Kepatuhan rantai pasok Permentan 33/2025 >= 30%)
```

---

## 5. Rencana Penerapan Bertahap (Next Steps)
1. **Penyimpanan Dokumen:** Berkas ini menjadi acuan spesifikasi tunggal (*Single Source of Truth*).
2. **Implementasi Backend:** Memperbarui service AI agar menerima payload `historical_context` RAG dan mengembalikan array objek fisik nyata.
3. **Pembersihan Frontend:** Menghapus seluruh konstanta koordinat kotak kaku di `templates/simulator.html`, `templates/spatial.html`, dan `mobile/index.html`, menggantinya dengan loop render dinamis yang dilengkapi filter layer.