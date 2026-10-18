# DIRECTIVE TEKNIS: INTEGRASI RASTER TILE LAYER GEE CANOPY GREENNESS PERSIS GAMBAR GOOGLE EARTH ENGINE

**Status:** Fitur Spasial Unggulan (Core Visual Differentiator)  
**Target:** 
1. `cloud_services/gee_service.py` & `app.py` (Backend API Tile URL)
2. `templates/pendaftaran.html` & `templates/spatial.html` (Frontend Leaflet Render)

---

## 1. MENGAPA RASTER ASLI GEE DIPERLUKAN?
Gambar referensi pengguna menunjukkan **citra raster kontinu dengan gradasi warna (*palette stretch*)**:
* Warna oranye/kuning mewakili nilai rendah (lahan terbuka/kanopi jarang).
* Warna hijau muda mewakili vegetasi sedang.
* Warna hijau tua pekat mewakili tegakan kanopi rapat berklorofil tinggi.

Mengganti poligon vektor kotak saat ini dengan **raster XYZ tile layer asli** memberikan bukti visual otentik bahwa sistem benar-benar mengolah citra satelit skala planet, bukan sekadar menggambar kotak buatan.

---

## 2. PENAMBAHAN ENDPOINT DI BACKEND (`app.py` & `cloud_services/gee_service.py`)

### Di `cloud_services/gee_service.py`:
```python
def get_canopy_ndvi_tile_url():
    """
    Menghasilkan URL ubin XYZ dari komposit Copernicus Sentinel-2
    menggunakan visualisasi palet GEE standar.
    """
    try:
        import ee
        # Koleksi Sentinel-2 Harmonized
        s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
              .filterDate('2025-01-01', '2026-10-01')
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
              .median())
        
        ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')
        
        # Palet gradasi persis seperti legenda GEE asli:
        vis_params = {
            'min': 0.2,
            'max': 0.85,
            'palette': ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850', '#00441b']
        }
        
        map_id = ndvi.getMapId(vis_params)
        return {
            "status": "success",
            "tile_url": map_id['tile_fetcher'].url_format
        }
    except Exception as e:
        # Fallback tile URL jika credentials GEE lokal offline:
        # Menggunakan ubin Sentinel-2 Cloudless global gratis
        return {
            "status": "fallback",
            "tile_url": "[https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/](https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/){z}/{y}/{x}.jpg"
        }

Di app.py:
Python

@app.route('/api/gee/canopy-tile-url', methods=['GET'])
def api_gee_canopy_tile_url():
    from cloud_services.gee_service import get_canopy_ndvi_tile_url
    return jsonify(get_canopy_ndvi_tile_url())

3. PERBAIKAN DI FRONTEND (templates/pendaftaran.html)

Ganti fungsi initNdviLayer agar memuat tile layer raster asli dan menampilkan legenda warna di peta:
JavaScript

let geeRasterTileLayer = null;

async function initNdviLayer() {
    if (!ndviLayerGroup) return;
    ndviLayerGroup.clearLayers();

    try {
        const res = await fetch('/api/gee/canopy-tile-url');
        const json = await res.json();
        const tileUrl = json.tile_url;

        // Pasang raster tile layer asli GEE
        geeRasterTileLayer = L.tileLayer(tileUrl, {
            maxZoom: 18,
            opacity: 0.70,
            attribution: '&copy; Google Earth Engine &bull; Copernicus Sentinel-2'
        });

        ndviLayerGroup.addLayer(geeRasterTileLayer);
    } catch (err) {
        console.warn("[Pendaftaran] Gagal memuat ubin GEE:", err);
    }
}

Penambahan Legenda Warna di Bawah Peta:
HTML

<div id="pendaftaranNdviLegend" class="absolute bottom-3 right-3 z-[400] px-3 py-2 rounded-2xl bg-slate-950/90 backdrop-blur-md border border-slate-700 text-[10px] font-mono text-slate-200 shadow-xl space-y-1.5">
    <div class="flex items-center justify-between gap-3 border-b border-slate-800 pb-1">
        <strong class="text-emerald-400">GEE Canopy Greenness (NDVI)</strong>
        <span class="text-[9px] text-slate-400">Sentinel-2</span>
    </div>
    <div class="w-48 h-3 rounded-full bg-gradient-to-r from-[#d73027] via-[#fee08b] via-[#a6d96a] via-[#1a9850] to-[#00441b] border border-slate-600"></div>
    <div class="flex justify-between text-[8.5px] text-slate-400 font-bold">
        <span>0.20 (Jarang)</span>
        <span>0.50 (Sedang)</span>
        <span>0.85+ (Rapat)</span>
    </div>
</div>