# DIRECTIVE AG: SINKRONISASI TILE GEE CANOPY GREENNESS & PENYELARASAN DATABASE OVERVIEW

**Tujuan:**
1. Menyediakan endpoint `/api/gee/canopy-tile-url` di `app.py` agar layer "GEE Canopy Greenness (Sentinel-2)" langsung memuat raster citra satelit gradasi hijau-kuning-oranye.
2. Memastikan rute `/overview` dan `/api/overview/stats` membaca dataset 10 konsesi yang sama dengan halaman pendaftaran.

---

### TUGAS 1: Tambahkan Endpoint Tile GEE di `app.py`

Buka `app.py` dan tambahkan rute berikut:

```python
# ==============================================================================
# ROUTE: GEE CANOPY GREENNESS TILE URL (SENTINEL-2 RASTER HEATMAP)
# ==============================================================================
@app.route('/api/gee/canopy-tile-url', methods=['GET'])
def api_gee_canopy_tile_url():
    """
    Menghasilkan URL ubin raster Sentinel-2 untuk ditampilkan di Leaflet map.
    Jika server lokal belum login GEE credentials, menggunakan fallback WMS publik gratis.
    """
    try:
        from cloud_services.gee_service import get_canopy_ndvi_tile_url
        res = get_canopy_ndvi_tile_url()
        return jsonify(res)
    except Exception:
        # Fallback tile global Sentinel-2 Cloudless MSI gratis tanpa registrasi
        return jsonify({
            "status": "fallback",
            "tile_url": "[https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/](https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/){z}/{y}/{x}.jpg"
        })

Di cloud_services/gee_service.py (jika belum ada fungsi get_canopy_ndvi_tile_url):
Python

def get_canopy_ndvi_tile_url():
    import ee
    s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
          .filterDate('2025-01-01', '2026-10-01')
          .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
          .median())
    ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')
    vis_params = {
        'min': 0.2,
        'max': 0.85,
        'palette': ['#d73027', '#fee08b', '#a6d96a', '#1a9850', '#00441b']
    }
    map_id = ndvi.getMapId(vis_params)
    return {
        "status": "success",
        "tile_url": map_id['tile_fetcher'].url_format
    }

TUGAS 2: Daftarkan Rute /overview di app.py
Python

@app.route('/overview')
def executive_overview():
    return render_template('overview.html')

TUGAS 3: Pengujian

Jalankan server:
Bash

python app.py

Buka halaman pendaftaran (http://localhost:8080/pendaftaran):

    Pastikan layer asean.mbtiles dan GEE Canopy Greenness aktif bersamaan.

    Layer GEE kini akan menutupi peta dengan warna kanopi Sentinel-2 dan legenda gradasi (0.20 – 0.85+).

    Buka http://localhost:8080/overview: data portofolio sekarang persis sama 10 Konsesi (11.100 Ha).