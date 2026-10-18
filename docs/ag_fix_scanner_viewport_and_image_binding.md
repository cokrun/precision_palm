# DIRECTIVE RESMI AG: PERBAIKAN DECOUPLING VIEWPORT SCANNER AI & BINDING CITRA (FIX FLOATING BOUNDING BOXES)

**Status:** Perbaikan Frontend Wajib (Critical Frontend Bugfix)  
**Target File:** `templates/spatial.html`, `static/js/spatial.js`, `templates/timelines.html`, `templates/simulator.html`, dan `mobile/index.html`.

---

## 1. MASALAH UTAMA PADA TAMPILAN VIEWPORT SCANNER

Sebagaimana terlihat pada `gambar_5.jpg`:
1. Viewport utama menampilkan teks `"No aerial drone evidence photo uploaded yet"`, namun SVG overlay tetap menggambar belasan kotak bounding box (`Palm Crown`, `Haul Road`) di atas layar kosong gelap.
2. Thumbnail foto `sawit-drone4` di galeri kiri sudah dipilih (checked), tetapi gambarnya tidak muncul pada viewport kanvas di sebelah kanan.

---

## 2. ATURAN LOGIKA WAJIB DI FRONTEND (ZERO FLOATING BOXES)

Terapkan 3 aturan ketat ini pada seluruh modul scanner AI:

### A. Strict Guard Clause: Tidak Ada Gambar = Tidak Ada Kotak
Pada fungsi render bounding box di `spatial.js`, `timelines.js`, dan `simulator.js`:

```javascript
// STREAMING_CHUNK:Enforcing strict viewport guard clause
function renderDynamicBoundingBoxes(entities, imageElementId, svgOverlayId) {
    const imgEl = document.getElementById(imageElementId);
    const svgOverlay = document.getElementById(svgOverlayId);
    
    if (!svgOverlay) return;

    // 1. KOSONGKAN TOTAL SVG SEBELUM MEMPROSES APAPUN
    svgOverlay.innerHTML = '';

    // 2. JIKA GAMBAR BELUM DIMUAT ATAU TIDAK ADA ELEMEN CITRA VALID
    if (!imgEl || !imgEl.src || imgEl.src.includes('undefined') || imgEl.naturalWidth === 0 || imgEl.style.display === 'none') {
        svgOverlay.style.display = 'none';
        return;
    }

    // 3. JIKA CITRA VALID, TAMPILKAN OVERLAY DAN GAMBARKAN KOTAK
    svgOverlay.style.display = 'block';

    if (!entities || entities.length === 0) return;

    entities.forEach(obj => {
        if (!obj.box_2d || obj.box_2d.length !== 4) return;
        
        const [ymin, xmin, ymax, xmax] = obj.box_2d;
        const topPct = (ymin / 1000) * 100;
        const leftPct = (xmin / 1000) * 100;
        const widthPct = ((xmax - xmin) / 1000) * 100;
        const heightPct = ((ymax - ymin) / 1000) * 100;

        let strokeColor = "#10b981"; // Emerald
        if (obj.cluster === "water_riparian") strokeColor = "#38bdf8";
        else if (obj.cluster === "fruit_organs") strokeColor = "#f59e0b";
        else if (obj.cluster === "weed_cover") strokeColor = "#f43f5e";
        else if (obj.cluster === "road_canal") strokeColor = "#a855f7";

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

        const text = document.createElementNS("[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)", "text");
        text.setAttribute("x", `${leftPct}%`);
        text.setAttribute("y", `${Math.max(topPct - 1.5, 3)}%`);
        text.setAttribute("fill", strokeColor);
        text.setAttribute("font-size", "10px");
        text.setAttribute("font-family", "monospace");
        text.setAttribute("font-weight", "bold");
        text.textContent = `${obj.label} [${Math.round((obj.confidence || 0.95) * 100)}%]`;

        svgOverlay.appendChild(rect);
        svgOverlay.appendChild(text);
    });
}

B. Binding Sinkron Antara Galeri Thumbnail & Viewport Utama

Ketika thumbnail (seperti sawit-drone4) diklik atau dipilih di panel kiri:

    Ambil URL biner gambar: /api/media/evidence/<evidence_id>.

    Setel elemen src viewport utama:

JavaScript

   const mainImg = document.getElementById('mainDroneDisplayImg');
   const emptyPlaceholder = document.getElementById('droneEmptyPlaceholder');
   
   mainImg.onload = function() {
       // Hanya jalankan pemindaian / render kotak SETELAH gambar benar-benar tampak
       mainImg.style.display = 'block';
       if (emptyPlaceholder) emptyPlaceholder.style.display = 'none';
       renderDynamicBoundingBoxes(currentPhotoEntities, 'mainDroneDisplayImg', 'aiReticleSvgOverlay');
   };
   mainImg.src = selectedPhotoUrl;
   

    Jika belum ada foto yang dipilih:

        Sembunyikan elemen <img>: mainImg.style.display = 'none';.

        Tampilkan droneEmptyPlaceholder.

        Bersihkan total SVG overlay: svgOverlay.innerHTML = '';.

C. Sinkronkan ke Seluruh 4 Modul Scanner AI

Pastikan perilaku guard clause ini aktif di:

    /spatial: Viewport ortofoto drone nadir 45m.

    /proses (Simulator): Viewport pemindaian koridor biofisika 3.79m.

    /timelines: Viewport galeri pemantauan mandor triwulan (Q1–Q4).

    /mobile: Viewport kamera in-situ mandor lapangan.