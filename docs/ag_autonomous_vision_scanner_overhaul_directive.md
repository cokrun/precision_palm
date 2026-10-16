# DIRECTIVE RESMI AG: PEROMBAKAN TOTAL SCANNER VISI AI DARI MOCKUP MENJADI SISTEM OTONOM BERORIENTASI MEMORI (REAL GEMINI 3.8 FLASH VISION + EPISODIC RAG)

**Status:** Perintah Eksekusi Wajib (Enforceable Architectural Directive)  
**Model Standar Produksi:** `gemini-3.8-flash` (Google AI Studio & Vertex AI Gemini API)  
**Tujuan:** Menghentikan segala bentuk kamuflase visual, menghapus total kotak statis fiktif, mengaktifkan pemanggilan multimodal Google Gemini 3.8 Flash Vision secara nyata, serta menyimpan pola pengalaman agen ke SQLite WAL dan Google BigQuery.

---

## 1. MASALAH FATAL YANG WAJIB DIHAPUS SEKETIKA

Di file `templates/simulator.html`, `templates/spatial.html`, `templates/timelines.html`, dan `mobile/index.html` (beserta file pendukung di `static/js/`):
* **HAPUS** seluruh array koordinat statis/mockup (seperti `defaultBoxes`, array `{x: 24, y: 12, ...}`).
* **HAPUS** mockup telemetri palsu yang memaksakan teks `🛸 Drone AGL: 45.0m | Pitch: -90°` pada foto darat horizontal.
* **HAPUS** perilaku di mana foto kolam/rawa diberi kotak `Sterile Buffer 2.0m [97%]`. Jika AI melihat air, AI harus melabelinya sebagai `[ 💧 Water Body / Riparian Pond ]`.

---

## 2. BACKEND: PEMANGGILAN REAL GEMINI 3.8 FLASH VISION (`ai_service.py` / `app.py`)

Ganti fungsi scanner tiruan dengan controller pemanggilan Google GenAI SDK menggunakan model **`gemini-3.8-flash`** yang mengembalikan format bounding box terstandarisasi:

```python
# STREAMING_CHUNK:Configuring Gemini 3.8 Flash Multimodal Real Scanner with Memory Anchor
import os
import json
import hashlib
from google import genai
from google.genai import types

# Model resmi yang aktif dan wajib digunakan
MODEL_VISION_ID = os.getenv("GEMINI_VISION_MODEL", "gemini-3.8-flash")

def scan_plantation_image_real(image_bytes: bytes, block_id: str, company_name: str, client_telemetry: dict) -> dict:
    """
    Eksekusi inferensi multimodal murni menggunakan Gemini 3.8 Flash.
    Menerima binary bytes foto asli dan mengembalikan koordinat objek nyata dalam skala 0 - 1000.
    """
    # 1. Validasi Anti-Fraud Hash Biner (Zero Re-use)
    photo_hash = hashlib.sha256(image_bytes).hexdigest()
    if check_if_hash_exists_in_db(photo_hash):
        return {
            "status": "error",
            "code": "FRAUD_PHOTO_REUSED",
            "message": "Foto ini telah terdaftar pada audit sebelumnya. Sesuai Permentan 33/2025, wajib mengambil foto fisik baru di lapangan."
        }

    # 2. Ambil Memori Pengalaman Blok Sebelumnya (Episodic RAG)
    historical_memory = retrieve_block_memory(block_id, limit=2)
    memory_context = "Belum ada audit sebelumnya (Siklus Perdana)."
    if historical_memory:
        last = historical_memory[0]
        memory_context = (
            f"Audit sebelumnya ({last.get('timestamp_iso')}): Teramati {last.get('observed_taxon')}. "
            f"Catatan agen: {last.get('learned_context_summary')}"
        )

    # 3. Rakit System Prompt Ketat untuk Gemini Vision
    prompt = f"""
Anda adalah Auditor Visi Spasial & Ekologis Precision Palm.
Tugas: Lakukan deteksi objek fisik nyata pada citra perkebunan ini dan kembalikan skema JSON murni.

KONTEKS MEMORI HISTORIS BLOK ({block_id}):
{memory_context}

TELEMETRI KAMERA DILAPORKAN SENSOR:
- Altitude Lapangan: {client_telemetry.get('altitude_m', 1.5)} meter
- Sudut Kemiringan: {client_telemetry.get('pitch_deg', 0.0)} derajat

ATURAN DETEKSI FISIK NYATA (JANGAN MENGARANG KOTAK FIKTIF):
1. Jika foto memperlihatkan AIR, RAWA, atau PARIT:
   - Buat bounding box pada area air tersebut dengan label 'Water Body / Wetland Canal', cluster 'water_riparian'.
   - BERIKAN PERINGATAN: Dilarang menanam tanaman sela rimpang di zona air!
2. Jika foto memperlihatkan SEMAK BELUKAR:
   - Beri label 'Natural Shrub / Non-Crop Cover', cluster 'weed_cover'.
3. Jika foto memperlihatkan BATANG SAWIT / ANATOMI POHON:
   - Beri label 'Palm Trunk Left/Right', cluster 'palm_anatomy'.
4. Jika foto memperlihatkan TANDAN BUAH:
   - Beri label 'FFB Fruit Bunch', cluster 'fruit_organs'.
5. Jika foto memperlihatkan UDARA DRONE (Tampak Atas):
   - Deteksi setiap tajuk pohon sawit: 'Palm Crown #1', 'Palm Crown #2', dst. Hitung populasi per hektar.
   - Deteksi jalur jalan tanah: 'Haul Road'.

Format koordinat box_2d adalah [ymin, xmin, ymax, xmax] dengan rentang angka normalisasi 0 hingga 1000.
KEMBALIKAN OUTPUT HANYA BERUPA JSON VALID.
"""

    client = genai.Client()
    response = client.models.generate_content(
        model=MODEL_VISION_ID,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )
    )

    result = json.loads(response.text)
    result["photo_sha256"] = photo_hash
    result["block_id"] = block_id
    result["company_name"] = company_name
    result["model_used"] = MODEL_VISION_ID

    # 4. Simpan ke Basis Data Pengalaman Agen (SQLite WAL & BigQuery)
    save_agent_experience_to_db(result)
    record_used_photo_hash(photo_hash, block_id, company_name)

    return result
3. FRONTEND: RENDER BOUNDING BOX DINAMIS DARI DATA JSON (BUKAN SVG STATIS)Di frontend JavaScript (simulator.js, spatial.js, mobile_camera.js):Kosongkan Kontainer Kotak Sebelum Deteksi:Ketika tombol Rescan AI diklik, bersihkan canvas/layer: svgOverlay.innerHTML = '';Loop Array Hasil Deteksi Riil:JavaScript// STREAMING_CHUNK:Rendering dynamic physical bounding boxes from API response
function renderDynamicBoundingBoxes(entities, imageWidth, imageHeight) {
    const svgOverlay = document.getElementById('aiReticleSvgOverlay');
    svgOverlay.innerHTML = ''; // Hapus seluruh elemen lama

    if (!entities || entities.length === 0) {
        return;
    }

    entities.forEach(obj => {
        // box_2d: [ymin, xmin, ymax, xmax] normalisasi 0 - 1000
        const [ymin, xmin, ymax, xmax] = obj.box_2d;
        const topPct = (ymin / 1000) * 100;
        const leftPct = (xmin / 1000) * 100;
        const widthPct = ((xmax - xmin) / 1000) * 100;
        const heightPct = ((ymax - ymin) / 1000) * 100;

        // Pilih warna berdasarkan cluster objek nyata
        let strokeColor = "#10b981"; // Emerald default
        if (obj.cluster === "water_riparian") strokeColor = "#38bdf8"; // Cyan untuk air
        else if (obj.cluster === "fruit_organs") strokeColor = "#f59e0b"; // Amber untuk buah TBS
        else if (obj.cluster === "weed_cover") strokeColor = "#f43f5e"; // Rose untuk gulma / rawa
        else if (obj.cluster === "road_canal") strokeColor = "#a855f7"; // Purple untuk jalan

        // Gambar elemen SVG Bounding Box Dinamis
        const rect = document.createElementNS("[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)", "rect");
        rect.setAttribute("x", `${leftPct}%`);
        rect.setAttribute("y", `${topPct}%`);
        rect.setAttribute("width", `${widthPct}%`);
        rect.setAttribute("height", `${heightPct}%`);
        rect.setAttribute("fill", "none");
        rect.setAttribute("stroke", strokeColor);
        rect.setAttribute("stroke-width", "2.5");
        rect.setAttribute("rx", "6");
        rect.classList.add("dynamic-ai-bbox", `cluster-${obj.cluster}`);

        // Label Badge
        const text = document.createElementNS("[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)", "text");
        text.setAttribute("x", `${leftPct}%`);
        text.setAttribute("y", `${Math.max(topPct - 1.5, 3)}%`);
        text.setAttribute("fill", strokeColor);
        text.setAttribute("font-size", "10px");
        text.setAttribute("font-family", "monospace");
        text.setAttribute("font-weight", "bold");
        text.textContent = `${obj.label} [${Math.round(obj.confidence * 100)}%]`;

        svgOverlay.appendChild(rect);
        svgOverlay.appendChild(text);
    });
}
Aktifkan Filter Layer Toggle:Sediakan tombol di bawah foto untuk menyembunyikan/menampilkan kelas tertentu (cluster-water_riparian, cluster-palm_anatomy, cluster-fruit_organs).4. PENYIMPANAN MEMORI EPISODIK AGEN KE DATABASE (agent_experience)Pastikan di database.py:Tabel agent_experience menyimpan:block_id, company_name, timestamp_isodetected_entities_json (seluruh koordinat kotak nyata)learned_context_summary (sintesis inferensi agen)discrepancy_score (apakah komoditas sesuai izin)Setiap kali ada pemindaian baru, data ini disimpan ke SQLite WAL dan dipancarkan ke Google BigQuery (precision_palm_dw.block_evidence_ledger).Pada pemindaian selanjutnya, data ini dimuat kembali sebagai anchor context (RAG) sehingga agen tidak mengulangi kesalahan dan mampu melacak dinamika perubahan lahan.5. PANDUAN PENGUJIAN AKHIR (SANITY CHECK)Jalankan python app.py.Buka gambar kolam/rawa (field_wetland_buffer.jpg) di /simulator atau /spatial $\rightarrow$ klik Rescan AI.HASIL WAJIB:Panggilan API mengarah ke model gemini-3.8-flash.Kotak merah Sterile Buffer 2.0m TIDAK BOLEH muncul di atas air.Muncul kotak biru cyan bertuliskan Water Body / Wetland Canal persis menutupi badan air.Muncul kotak semak pada vegetasi tepi.Kotak-kotak tersebut harus mengikuti kontur objek di foto asli, bukan kotak statis 3 biji yang kaku.