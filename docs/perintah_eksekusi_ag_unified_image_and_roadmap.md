# INSTRUKSI EKSEKUSI RESMI UNTUK AG: PERBAIKAN ALIRAN CITRA 4 TITIK & DINAMISASI RATIFIKASI ROADMAP

**Perihal:** Perbaikan Fitur Galeri Foto Spatial, Penyatuan Alur Citra 4 Modul, dan Dinamisasi Gerbang Ratifikasi Roadmap  
**Dasar Evaluasi:**
* Masalah Galeri Spatial: Foto terdaftar di panel kiri gagal dimuat ke viewport kanan dan badge scan macet dalam status *Scanning*.
* Halaman Roadmap: Perlu dihubungkan secara dinamis dengan hasil audit 4 tahap dan tombol ratifikasi wajib mengeksekusi penulisan ke database.
* Berkas Target:
  1. `static/js/spatial.js` & `templates/spatial.html`
  2. `static/js/roadmap.js` & `templates/roadmap.html`
  3. `app.py` (Endpoint Media & Ratifikasi Asesor)

---

## 🛠️ BAGIAN 1: PERBAIKAN FITUR GALERI FOTO DI HALAMAN SPATIAL

### 1.1 Perbaiki Event Handler Seleksi Foto di `static/js/spatial.js`
Buka `static/js/spatial.js` dan temukan fungsi pemilihan foto galeri (misal `selectDronePhoto` atau `renderDroneGallery`). Pastikan saat thumbnail diklik:

1. Atribut `src` pada elemen `<img>` utama (`#verifPhotoImg`) diperbarui ke URL citra yang valid:
   
```javascript
   function selectDronePhoto(photoId, photoUrl, photoName) {
       const imgEl = document.getElementById('verifPhotoImg');
       const emptyStateEl = document.getElementById('emptyEvidenceState');
       const scanBadge = document.getElementById('badgeAiScanResult');
       const laserBar = document.getElementById('spatialLaserSweepBar');
       const photoLabelEl = document.getElementById('lblCapturedPhotoName');

       if (!imgEl) return;

       // 1. Matikan indikator scanning otomatis
       if (laserBar) laserBar.classList.add('hidden');
       if (scanBadge) {
           scanBadge.textContent = "Foto Siap";
           scanBadge.className = "px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700";
       }

       // 2. Tampilkan elemen citra dan sembunyikan empty state
       if (emptyStateEl) emptyStateEl.classList.add('hidden');
       imgEl.style.display = 'block';
       imgEl.classList.remove('hidden');

       // 3. Muat sumber gambar yang dipilih
       imgEl.src = photoUrl;
       if (photoLabelEl) photoLabelEl.textContent = photoName || "Drone Orthophoto Active";

       // 4. Muat bounding box yang tersimpan untuk foto ini (tanpa panggil ulang AI)
       loadCachedBoxesForPhoto(photoId);
   }
   

    Perbaiki Handler Error Citra:

JavaScript

   function handleEmptyEvidenceState(imgElement) {
       // Hanya sembunyikan jika memang URL benar-benar gagal dimuat
       console.warn("[Spatial] Gagal memuat URL citra:", imgElement.src);
       imgElement.style.display = 'none';
       const emptyState = document.getElementById('emptyEvidenceState');
       if (emptyState) emptyState.classList.remove('hidden');

       const scanBadge = document.getElementById('badgeAiScanResult');
       if (scanBadge) {
           scanBadge.textContent = "Belum Ada Foto";
           scanBadge.className = "px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400 border border-slate-700";
       }
   }
   

    Hubungkan Tombol [ Rescan AI ]:
    Pemindaian hanya berjalan saat tombol Rescan AI ditekan secara manual. Jangan jalankan pemindaian otomatis di event onload gambar galeri lama.

🛠️ BAGIAN 2: PENYELARASAN PEMBACAAN CITRA DI 4 TITIK

Pastikan keempat modul membaca dan menulis berkas citra secara konsisten:

    spatial (UAV Nadir Orthophoto):

        Menyimpan dan memuat foto dengan flag perspective_mode = 'AERIAL_DRONE'.

        Endpoint unggah: POST /api/evidence/upload.

    simulator (In-Silico Core):

        Mengambil foto aktif dari galeri drone untuk mengekstrak estimasi bukaan kanopi (PAR).

    mobile (In-Situ Mandor PWA):

        Menyimpan foto kamera HP dengan flag perspective_mode = 'TERRESTRIAL_IN_SITU'.

        Melampirkan koordinat EXIF GPS dan hasil uji validasi cuaca satelit BMKG.

    timelines (Surveilans Triwulan):

        Menampilkan kartu Q1 hingga Q4 berdasarkan catatan yang ada di tabel inspection_evidence sesuai kuartal yang tersimpan.

🛠️ BAGIAN 3: DINAMISASI HALAMAN ROADMAP (STAGE 4 RATIFIKASI)
3.1 Hubungkan Rangkuman 4-Tahap dengan Dossier Aktif

Buka static/js/roadmap.js dan pastikan fungsi renderConsolidatedDossier(dossierId) mengambil data riil dari backend:

    Panggil Data Agregasi Dossier:

JavaScript

   async function loadRoadmapDossier(dossierId) {
       try {
           const res = await fetch(`/api/dossier/${encodeURIComponent(dossierId)}/roadmap-summary`);
           if (res.ok) {
               const data = await res.json();
               updateRoadmapUiElements(data);
           }
       } catch (e) {
           console.error("[Roadmap] Gagal memuat ringkasan dossier:", e);
       }
   }
   

    Perbarui Data Kartu Master Docket:

        Stage 1: Tampilkan Nomor HGU, NOP PBB, dan Luas Ha riil dari tabel dossiers.

        Stage 2A: Tampilkan Deforestasi Hansen (0.00 Ha) dan kemiringan lereng dari spatial_telemetry.

        Stage 2B: Tampilkan nilai LER aktual, komoditas sela terpilih, dan penghematan lahan dari in_silico_simulations.

        Stage 3: Tampilkan jumlah kuartal yang terisi bukti foto mandor dari inspection_evidence.

3.2 Fungsionalkan Tombol Ratifikasi Sidang Asesor

Buka formulir sidang asesor di bagian bawah templates/roadmap.html:
HTML

<form id="formAssessorRatification" onsubmit="handleAssessorRatification(event)">
    <input type="text" id="inpAssessorName" required class="..." placeholder="Nama Lead Assessor & Gelar">
    <textarea id="txtAssessorNotes" required class="..." placeholder="Catatan Pertimbangan Sidang"></textarea>
    <button type="submit" id="btnSubmitRatification" class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl text-xs flex items-center gap-2 cursor-pointer shadow-lg">
        <span>🔒</span> <span>Ratify &amp; Lock SHA-256 Statutory Seal</span>
    </button>
</form>

Tambahkan fungsi eksekusi di roadmap.js:
JavaScript

async function handleAssessorRatification(event) {
    event.preventDefault();

    const dossierId = getActiveDossierId() || "EST-MDN-001";
    const assessorName = document.getElementById('inpAssessorName')?.value;
    const notes = document.getElementById('txtAssessorNotes')?.value;
    const btn = document.getElementById('btnSubmitRatification');

    if (btn) btn.disabled = true;

    try {
        const payload = {
            dossier_id: dossierId,
            lead_assessor_name: assessorName,
            deliberation_notes: notes,
            final_verdict: "APPROVED_CERTIFIED"
        };

        const res = await fetch('/api/roadmap/ratify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const json = await res.json();
        if (json.status === 'success') {
            alert("✓ Berkas resmi disahkan! Paspor Kepatuhan Statuter dan Segel SHA-256 telah diterbitkan.");
            // Perbarui tampilan stempel dan segel SHA-256
            if (json.sha256_seal) {
                document.getElementById('dispCloudKmsSeal').textContent = json.sha256_seal;
            }
            window.location.reload();
        } else {
            alert("Gagal meratifikasi: " + (json.message || "Terjadi kesalahan"));
        }
    } catch (err) {
        alert("Kesalahan jaringan: " + err.message);
    } finally {
        if (btn) btn.disabled = false;
    }
}

🛠️ BAGIAN 4: TAMBAHKAN ENDPOINT DI app.py

Buka app.py dan daftarkan 2 endpoint pendukung berikut:
Python

# ==============================================================================
# ENDPOINT: SUMMARY ROADMAP 4-TAHAP PER DOSSIER
# ==============================================================================
@app.route('/api/dossier/<dossier_id>/roadmap-summary', methods=['GET'])
def api_dossier_roadmap_summary(dossier_id):
    try:
        from database_schema_engine import get_db_connection
        conn = get_db_connection()

        # Ambil dossier
        d = conn.execute("SELECT * FROM dossiers WHERE dossier_id = ?", (dossier_id,)).fetchone()
        if not d:
            conn.close()
            return jsonify({"status": "error", "message": "Dossier tidak ditemukan"}), 404

        # Ambil telemetri satelit (Stage 2A)
        st = conn.execute("SELECT * FROM spatial_telemetry WHERE dossier_id = ? ORDER BY recorded_at DESC LIMIT 1", (dossier_id,)).fetchone()

        # Ambil simulasi LER (Stage 2B)
        sim = conn.execute("SELECT * FROM in_silico_simulations WHERE dossier_id = ? ORDER BY calculated_at DESC LIMIT 1", (dossier_id,)).fetchone()

        # Ambil hitungan bukti surveilans (Stage 3)
        ev_count = conn.execute("SELECT COUNT(DISTINCT quarter_cycle) FROM inspection_evidence WHERE dossier_id = ?", (dossier_id,)).fetchone()[0]

        # Ambil sertifikasi jika sudah disahkan (Stage 4)
        cert = conn.execute("SELECT * FROM certification_audits WHERE dossier_id = ?", (dossier_id,)).fetchone()

        conn.close()

        return jsonify({
            "status": "success",
            "dossier": dict(d),
            "stage2a": dict(st) if st else None,
            "stage2b": dict(sim) if sim else None,
            "stage3_quarters_count": ev_count,
            "certification": dict(cert) if cert else None
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==============================================================================
# ENDPOINT: RATIFIKASI FORMAL ASESOR (STAGE 4 COMMIT)
# ==============================================================================
@app.route('/api/roadmap/ratify', methods=['POST'])
def api_roadmap_ratify():
    try:
        import hashlib
        from datetime import datetime
        from database_schema_engine import get_db_connection

        data = request.get_json() or {}
        dossier_id = data.get('dossier_id')
        lead_assessor = data.get('lead_assessor_name', 'Lead Assessor ISPO/EUDR')
        notes = data.get('deliberation_notes', 'Unconditional Pass')

        if not dossier_id:
            return jsonify({"status": "error", "message": "dossier_id wajib disertakan"}), 400

        conn = get_db_connection()

        # Buat stempel SHA-256 mutlak
        raw_seed = f"{dossier_id}:{lead_assessor}:{datetime.utcnow().isoformat()}:PRECISION_PALM_EUDR_ART9"
        sha256_digest = hashlib.sha256(raw_seed.encode('utf-8')).hexdigest().upper()
        audit_id = f"AUD-{dossier_id}-2026"

        # Simpan ke tabel certification_audits
        conn.execute("""
            INSERT INTO certification_audits (
                audit_id, dossier_id, audit_year, lead_assessor_name,
                assessor_registration_no, final_verdict, sla_180d_countdown_expiry,
                immutable_dossier_sha256, eudr_traces_nt_dds_json, public_validation_qr_url
            ) VALUES (?, ?, 2026, ?, 'ASSES-ISPO-EUDR-2026', 'APPROVED_CERTIFIED',
                     datetime('now', '+180 days'), ?, '{}', ?)
            ON CONFLICT(dossier_id) DO UPDATE SET
                lead_assessor_name = excluded.lead_assessor_name,
                final_verdict = 'APPROVED_CERTIFIED',
                immutable_dossier_sha256 = excluded.immutable_dossier_sha256,
                certified_at = CURRENT_TIMESTAMP;
        """, (audit_id, dossier_id, lead_assessor, sha256_digest, f"/validasi/{dossier_id}"))

        # Update status permohonan ke VERIFIED
        conn.execute("UPDATE dossiers SET status_permohonan = 'VERIFIED' WHERE dossier_id = ?", (dossier_id,))

        conn.commit()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Ratifikasi berhasil disimpan",
            "audit_id": audit_id,
            "sha256_seal": sha256_digest
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

🧪 PENGUJIAN & VERIFIKASI

    Buka http://localhost:8080/spatial:

        [ ] Klik salah satu foto di panel kiri galeri → foto harus langsung tampil di viewport kanan.

        [ ] Empty state otomatis tersembunyi.

        [ ] Badge tidak lagi terjebak di status pemindaian berulang.

    Buka http://localhost:8080/roadmap:

        [ ] Kartu Master Docket di sebelah kiri terisi data riil dari database.

        [ ] Isi nama asesor dan klik [ Ratify & Lock SHA-256 Statutory Seal ].

        [ ] Notifikasi sukses muncul dan hash SHA-256 tercetak resmi di kartu paspor kanan.