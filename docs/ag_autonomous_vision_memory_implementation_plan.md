# DOKUMEN IMPLEMENTASI TEKNIS & ARSITEKTUR SISTEM
## Autonomous Agent Memory RAG, Real Multi-Object HUD (15–25 Entitas), Matriks 44 Variabel, dan Permentan No. 33 Tahun 2025

**Status:** Dokumen Rekayasa Sistem Resmi (Engineered Specification Document)  
**Tujuan:** Penghapusan total seluruh bounding box statis/palsu di 4 halaman (`/spatial`, `/simulator`, `/timelines`, `/mobile`), aktivasi agen cerdas berorientasi memori (*Episodic RAG Experience Loop*), deteksi objek fisik nyata (15–25 entitas) dengan filter layer, dan pembaruan seluruh sistem ke dasar hukum **Permentan No. 33 Tahun 2025 (ISPO Baru)**.

---

### 1. RINGKASAN ARSITEKTUR SISTEM

Sistem Precision Palm mengintegrasikan arsitektur agen otonom berbasis *Episodic Memory RAG* untuk audit biofisika, topologi perkebunan kelapa sawit, dan kepatuhan regulasi terestrial/aerial.

1. **Episodic Memory RAG Store:**
   - Tabel `agent_experience` di SQLite dengan mode WAL (*Write-Ahead Logging*) dan indeks `idx_agent_exp_block`.
   - Replikasi data telemetri historis ke BigQuery Data Warehouse `precision_palm_dw.agent_experience`.
2. **Konteks Memori Injeksi:**
   - Mengambil 3 riwayat inspeksi sebelumnya per blok kebun (`block_id`) untuk disuntikkan ke prompt Gemini Flash Vision.
3. **Structured Contract JSON:**
   - 15–25 entitas fisik nyata dengan atribut klaster: `palm_anatomy`, `fruit_organs`, `root_circle`, `floor_mulch`, `palm_canopy`, `infrastructure`, `empty_gap`.
   - Matriks 44 Variabel Agronomi ($C1$–$C6$).
   - Skor diskrepansi otonom ($>0.80$) saat takson teramati menyimpang dari deklarasi awal (misal Jagung vs Jahe Merah).
4. **Pembaruan Regulasi Statuter:**
   - Seluruh rujukan hukum ISPO dimutakhirkan secara konsisten ke **Permentan No. 33 Tahun 2025 (ISPO Baru)**.

---

### 2. LOGIKA BACKEND & PROMPT AGENT MEMORY LOOP (`ai_service.py`)

Agen tidak bekerja secara *stateless*. Sebelum memanggil Gemini Flash Vision, agen mengambil pengalaman audit blok sebelumnya:

```python
def retrieve_block_memory(block_id: str, limit: int = 3) -> list:
    """Mengambil riwayat pengalaman audit sebelumnya untuk konteks RAG agen."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT declared_crop, observed_taxon, discrepancy_score, 
               learned_context_summary, timestamp_iso, diagnostic_matrix_json
        FROM agent_experience 
        WHERE block_id = ? 
        ORDER BY created_at DESC LIMIT ?
    """, (block_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def build_agent_vision_prompt(block_id: str, historical_memory: list, telemetry_4d: dict) -> str:
    memory_text = "NIL (First Audit Cycle)"
    if historical_memory:
        last = historical_memory[0]
        memory_text = (
            f"Previous Audit ({last['timestamp_iso']}): Declared={last['declared_crop']}, "
            f"Observed={last['observed_taxon']}, Discrepancy={last['discrepancy_score']}. "
            f"Learned Notes: {last['learned_context_summary']}"
        )
        
    return f"""
Anda adalah Agen Otonom Precision Palm (Bio-Ecological & RegTech Vision Auditor).
Lakukan analisis spasial 4D mendalam atas citra kebun kelapa sawit berikut.

KONTEKS MEMORI HISTORIS BLOK ({block_id}):
{memory_text}

TELEMETRI SENSOR 4D:
- Latitude: {telemetry_4d.get('lat', 0.824102)} | Longitude: {telemetry_4d.get('lng', 99.561214)}
- Altitude AGL: {telemetry_4d.get('altitude_m', 1.45)} m
- Sensor Pitch: {telemetry_4d.get('pitch_deg', -12.0)}°
- Capture Mode: {'AERIAL_DRONE' if telemetry_4d.get('altitude_m', 1.45) > 15.0 else 'TERRESTRIAL_IN_SITU'}

ATURAN DETEKSI OBJEK FISIK (JANGAN MEMBUAT KOTAK FIKTIF):
1. Jika AERIAL_DRONE (Z > 15m): Deteksi setiap tajuk pohon sawit individual ('Palm Crown #N'), jalur jalan kebun ('Haul Road'), parit air ('Canal'), dan celah kosong ('Missing Stand'). Hitung populasi riil (136-143 pokok/Ha).
2. Jika TERRESTRIAL_IN_SITU (Z <= 2m): Deteksi batang sawit kiri/kanan ('Palm Trunk A/B'), tandan buah ('FFB Ripe/Unripe'), piringan tanah bersih lingkaran batang ('Weed-Free Root Buffer'), dan tumpukan pelepah ('Pruned Frond Mulch').
3. KETERTELUSURAN BADAN AIR: Jika terdeteksi parit/kolam air, tandai sebagai 'Riparian Water Body' dan BERIKAN STATUS DILARANG TANAM RIMPANG (Risiko busuk akar).
4. KETIDAKSESUAIAN KOMODITAS (DISCREPANCY CHECK): Bandingkan komoditas teramati dengan deklarasi memori. Jika terdaftar Jagung tetapi teramati herba rimpang Jahe, laporkan selisihnya pada discrepancy_score (>0.80).

WAJIB MENGEMBALIKAN OUTPUT SESUAI STRUKTUR JSON BAKU (MATRIKS 44 VARIABEL & ENTITAS NYATA).
"""
```

---

### 3. CONTRACT SCHEMA JSON RESMI (MATRIKS 44 VARIABEL & 15–25 OBJEK)

Gemini Flash Vision mengembalikan payload terstruktur dengan skema berikut:

```json
{
  "block_id": "EST-MDN-001-BLOK-A",
  "perspective_4d": {
    "capture_mode": "TERRESTRIAL_IN_SITU",
    "altitude_agl_m": 1.45,
    "sensor_pitch_deg": -12.4,
    "coordinates_wgs84": {"lat": 0.824102, "lng": 99.561214},
    "classification": "Close-up Canopy & Ground Floor"
  },
  "physical_entities": [
    {"id": "obj_01", "label": "Palm Trunk Left", "cluster": "palm_anatomy", "box_2d": [210, 110, 890, 310], "confidence": 0.98},
    {"id": "obj_02", "label": "Palm Trunk Right", "cluster": "palm_anatomy", "box_2d": [230, 710, 880, 910], "confidence": 0.97},
    {"id": "obj_03", "label": "FFB Ripe Bunch #1", "cluster": "fruit_organs", "box_2d": [340, 240, 480, 320], "confidence": 0.95},
    {"id": "obj_04", "label": "FFB Mature Bunch #2", "cluster": "fruit_organs", "box_2d": [360, 700, 490, 770], "confidence": 0.94},
    {"id": "obj_05", "label": "Clean Root Buffer (2.0m)", "cluster": "root_circle", "box_2d": [750, 120, 950, 410], "confidence": 0.99},
    {"id": "obj_06", "label": "Clean Root Buffer (2.0m)", "cluster": "root_circle", "box_2d": [760, 680, 960, 930], "confidence": 0.98},
    {"id": "obj_07", "label": "Pruned Frond Mulch Pile", "cluster": "floor_mulch", "box_2d": [680, 360, 910, 640], "confidence": 0.93},
    {"id": "obj_08", "label": "Active Intercrop Alley (3.79m)", "cluster": "floor_mulch", "box_2d": [420, 310, 900, 680], "confidence": 0.96}
  ],
  "diagnostic_matrix_44": {
    "c1_geospatial_4d": {
      "var_01_longitude": 99.561214, "var_02_latitude": 0.824102,
      "var_03_altitude_agl_m": 1.45, "var_04_timestamp_iso": "2026-10-16T15:30:00Z",
      "var_05_camera_pitch_deg": -12.4, "var_06_ground_elevation_asl_m": 142.0,
      "var_07_terrain_slope_deg": 4.5, "var_08_distance_to_pippib_m": 4310.0
    },
    "c2_crop_and_morphology": {
      "var_09_inferred_taxon": "Zingiber officinale var. rubrum",
      "var_10_discrepancy_score": 0.02,
      "var_11_canopy_height_cm": 52.4,
      "var_12_growth_stage": "Vegetative Expansion (Bulan ke-4)",
      "var_13_foliar_aspect_ratio": 5.8,
      "var_14_ridge_width_cm": 60.0,
      "var_15_ground_cover_pct": 78.5,
      "var_16_noxious_weed_pct": 4.2
    },
    "c3_palm_physiology_and_pathology": {
      "var_17_root_clearance_m": 2.05,
      "var_18_tillage_violation": false,
      "var_19_stand_age_years": 7.5,
      "var_20_lai": 4.25,
      "var_21_par_transmission_pct": 35.8,
      "var_22_foliar_spad": 82.4,
      "var_23_nutrient_vector": "OPTIMAL (N-K Balanced)",
      "var_24_ganoderma_prob": 0.00
    },
    "c4_hydrology_soil_carbon": {
      "var_25_riparian_distance_m": 62.5,
      "var_26_turbidity_ntu": 18.2,
      "var_27_usda_cn_post": 64.0,
      "var_28_recharge_m3_ha_yr": 8050.0,
      "var_29_mop_compensation_kg_ha": 75.0,
      "var_30_urea_saved_kg_ha": 141.3,
      "var_31_ler": 1.48,
      "var_32_fips_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    "c5_genetics_pollination_castration": {
      "var_33_genetic_pedigree": "DxP 540 NG (PPKS New Generation)",
      "var_34_pollinator_density_per_ha": 28400,
      "var_35_male_inflorescence_retention": "Compliant (Reservoir Bunga Jantan Terjaga)",
      "var_36_fruit_set_pct": 84.2,
      "var_37_castration_status": "Sanitized (Ablasi Bunga Betina TBM Tuntas)"
    },
    "c6_lsu_frond17_etc_ispo2025": {
      "var_38_lsu_frond_phyllotaxis": "Frond-17 Confirmed (Sampel Baku TM)",
      "var_39_leaf_nutrient_matrix": {"N_pct": 2.84, "K_pct": 1.32, "Mg_pct": 0.28},
      "var_40_micronutrient_vector": {"boron_ppm": 21.5, "status": "Normal (Little Leaf Negative)"},
      "var_41_evapotranspiration_etc_mm_yr": 1284.0,
      "var_42_peat_water_table_cm": -48.0,
      "var_43_circular_mulch_application": "Aplikasi TKKS 25 t/Ha Terverifikasi",
      "var_44_ispo_permentan_33_2025_mass_balance_tier": "Tier-1 (>30% Certified FFB Inflow)"
    }
  },
  "agent_experience_summary": "Blok A konsesi Mandailing Natal menunjukkan konsistensi fenologi Jahe Merah bulan ke-4. Nilai klorofil daun pelepah-17 optimum (82.4 SPAD) tanpa gejala defisiensi K. Piringan steril 2.05m terjaga rapi dengan nihil nekrosis Ganoderma. LER dikunci pada 1.48x."
}
```

---

### 4. IMPLEMENTASI FRONTEND PADA 4 HALAMAN UTAMA

#### A. Halaman `/mobile` (PWA Handheld Mandor)
- **Hapus Seluruh Bounding Box Statis:** Seluruh array koordinat kaku dibersihkan dari `mobile/index.html` dan `mobile/js/mobile_camera.js`.
- **Render Kanvas Dinamis:** Berdasarkan `physical_entities` dari respon AI/ground truth.
- **Filter Layer Bar di Bawah Viewfinder:**
  - `[🌴 Anatomi Pokok (2)]` (Emerald)
  - `[🍇 Organ Buah / TBS (2)]` (Amber)
  - `[⭕ Piringan Steril (2)]` (Rose)
  - `[🍂 Mulsa & Lorong (2)]` (Teal)
- **Pita Telemetri 4D di Atas Kamera:**
  `[ 🛰️ 4D: 0.824102°N, 99.561214°E | Alt: 1.45m Handheld | SPAD: 82.4 | Ganoderma: 0.0% ]`
- **Penyimpanan Pengalaman Otomatis (RAG Loop):**
  Deteksi tersimpan di IndexedDB (`inspection_reports`) dan dikirim ke endpoint `/api/agent/experience` secara otomatis.

#### B. Halaman `/spatial` (Drone Aerial & Satelit GEE)
- **Mode Deteksi Aerial:** Mendeteksi 18 entitas nyata (Crowns 1–15, Haul Road, Drainage Canal, Missing Stand).
- **Penghitung Tegakan Riil:** `Populasi Terhitung: 138 Pokok/Ha (Sesuai Standar Segitiga 9.0m)`.
- **Korelasi Triangulasi Satelit GEE:**
  - NDVI Sentinel-2 (0.784) vs Klorofil Pelepah-17 (82.4 SPAD).
  - NDMI Kelembapan Satelit (0.412) vs Kelembapan Tanah Pori Riil.
- **Proteksi Sempadan Air Riparian:** Poligon cyan transparan mengunci aturan:
  `[STATUS: DILARANG TANAM RIMPANG — SEMPADAN AIR DILINDUNGI]`.
- **Cluster Layer HUD Toggles:** Tombol interaktif untuk menyaring klaster: `palm`, `infra`, `root`, `mulch`, `gap`.

#### C. Halaman `/proses` (Simulator Biofisika In-Silico)
- **Tombol Impor Telemetri Agen:** `⚡ [Impor Pengalaman Terkini Agen AI (EST-MDN-001)]`.
  - Mengunci Stand Age 7.5y, LAI 4.25, DxP 540 NG (PPKS), MOP +75kg, Ganoderma 0.0%, Piringan 2.05m, LER 1.48x (+48%).
- **Panel Matriks 44 Variabel Telemetri:** `#matrix44TelemetryPanel` menyajikan 6 klaster variabel lengkap ($C1$–$C6$).
- **Panel Nalar Bio-Ekologis 4 Lapis:**
  - *Filter Cahaya:* Radiasi tembus PAR pelepah sawit 35.8% (644.4 $\mu\text{mol/m}^2/\text{s}$) presisi untuk tanaman skiofit Zingiberaceae.
  - *Filter Tanah & Air:* Lempung berpasir gembur dengan NDMI 0.412 bebas risiko genangan busuk rimpang.
  - *Filter Non-Agresi Hara:* Jahe menyerap hara di lorong kedalaman 20 cm tanpa mengganggu akar serabut pokok sawit, didukung kompensasi pupuk MOP +75 kg/Ha (defisit panen TBS sawit hanya 1.22% $\le$ 4.5%).
  - *Filter Nilai Pasar:* Sifat living storage umbi rimpang hingga 12 bulan memberi bantalan finansial +Rp 38.4 Juta/Ha/thn bagi keluarga pekebun.

#### D. Halaman `/timelines` (Surveilans Triwulanan & Audit Regulasi)
- **Pemeriksaan Forensik Discrepancy:**
  - Menampilkan `#forensicDiscrepancyCard` saat takson teramati menyimpang ($0.85 > 0.80$, Jagung vs Jahe Merah).
  - Sistem menerbitkan peringatan amandemen perizinan dan mengalihkan kompensasi pupuk ke kalium (+75 kg MOP/Ha) secara otonom.
- **Kepatuhan Permentan No. 33 Tahun 2025 (ISPO Baru):**
  - Grid Tier-1 Statutory Badges:
    - *Siklus ISPO:* Valid 5 Tahun (Penilikan Tahunan Aktif)
    - *Mass Balance:* 30% Serapan TBS Tersertifikasi Lolos
    - *Audit Sosial:* Nol Pekerja Anak & Hak Tenaga Kerja Terverifikasi
    - *Legalitas Tanah:* e-STDB Pekebun Swadaya Terintegrasi

---

### 5. PROTOKOL VERIFIKASI PENGUJIAN AKHIR

1. **Endpoint Testing:**
   - `/api/agent/experience` (GET & POST) $\rightarrow$ HTTP 200 OK.
   - `/api/ai/scan-image` $\rightarrow$ HTTP 200 OK dengan 44-Variable Matrix & 15–25 physical entities.
2. **Frontend UI Testing:**
   - `/mobile` $\rightarrow$ Bounding box nyata terikat klaster; filter toggle dinamis; pita 4D aktif.
   - `/spatial` $\rightarrow$ 18 entitas drone, 138 Pokok/Ha counter, poligon cyan sempadan air riparian, GEE overlay.
   - `/proses` $\rightarrow$ Tombol impor mengunci data agen; matriks 44 variabel tampil lengkap; 4 filter alami aktif.
   - `/timelines` $\rightarrow$ Forensic Discrepancy Card ($0.85 > 0.80$); 4 badge Permentan No. 33 Tahun 2025.
3. **Statutory Citations Verification:**
   - Nol rujukan usang ke `38/2020` di seluruh codebase.
   - Semua rujukan hukum ISPO mengutip **Permentan No. 33 Tahun 2025**.