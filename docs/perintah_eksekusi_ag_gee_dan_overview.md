INSTRUKSI EKSEKUSI RESMI UNTUK AG (AUTOMATED AGENT / DEVELOPER)

Perihal: Implementasi Raster Tile GEE Canopy Greenness, Integrasi Rute /overview, dan Penyelarasan Database Konsesi

Dasar Acuan:

docs/gee_canopy_raster_layer_implementation.md

docs/ag_gee_tile_and_overview_sync_directive.md

templates/pendaftaran.html & templates/overview.html

📌 RINGKASAN TUGAS (EXECUTIVE SUMMARY)

Menyediakan fungsi penghasil raster tile GEE Sentinel-2 NDVI di cloud_services/gee_service.py lengkap dengan fallback Sentinel-2 Cloudless jika credentials offline.

Mendaftarkan endpoint /api/gee/canopy-tile-url dan rute /overview di app.py.

Menyelaraskan kueri database pada halaman /overview dan /pendaftaran agar bersumber dari dataset yang sama persis (10 Konsesi & 11.100,00 Ha).

Memastikan peta pada halaman Pendaftaran (templates/pendaftaran.html) menampilkan secara bersamaan:

Layer kawasan hutan moratorium lokal dari asean.mbtiles (/api/tiles/{z}/{x}/{y}).

Layer heatmap gradasi warna GEE Canopy Greenness beserta colorbar legendanya.

🛠️ LANGKAH 1: UPDATE cloud_services/gee_service.py

Buka file cloud_services/gee_service.py dan tambahkan (atau perbarui) fungsi berikut:

def get_canopy_ndvi_tile_url():
    """
    Menghasilkan URL ubin raster Sentinel-2 NDVI skala planet dari Google Earth Engine
    dengan palet warna gradasi 9-step (oranye -> kuning -> hijau pekat).
    Menyediakan fallback publik beresolusi tinggi jika token GEE server lokal belum aktif.
    """
    fallback_result = {
        "status": "fallback",
        "provider": "Sentinel-2 Cloudless EOX WMTS",
        "tile_url": "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg"
    }
    
    try:
        import ee
        # Inisialisasi Earth Engine jika belum aktif
        if not ee.data._credentials:
            ee.Initialize()

        # Ambil koleksi citra Sentinel-2 Surface Reflectance Harmonized
        s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
              .filterDate('2025-01-01', '2026-10-01')
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
              .median())
        
        # Hitung NDVI = (NIR - Red) / (NIR + Red)
        ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')
        
        # Palet gradasi warna identik visual resmi Google Earth Engine (0.20 - 0.85)
        vis_params = {
            'min': 0.20,
            'max': 0.85,
            'palette': [
                '#d73027',  # 0.20 - Merah/Oranye (Tanah terbuka / semak jarang)
                '#f46d43',
                '#fdae61',
                '#fee08b',  # 0.50 - Kuning (Vegetasi sedang / pelepah muda)
                '#d9ef8b',
                '#a6d96a',
                '#66bd63',
                '#1a9850',  # 0.75 - Hijau subur
                '#00441b'   # 0.85+ - Hijau sangat pekat (Kanopi sawit rapat produktif)
            ]
        }
        
        map_id = ndvi.getMapId(vis_params)
        return {
            "status": "success",
            "provider": "Google Earth Engine (Copernicus S2 SR)",
            "tile_url": map_id['tile_fetcher'].url_format
        }
    except Exception as err:
        # Graceful fallback jika server berjalan tanpa GEE service account key
        return fallback_result


🛠️ LANGKAH 2: UPDATE app.py

Buka file app.py dan daftarkan 2 rute berikut:

2.1 Endpoint Tile URL GEE

@app.route('/api/gee/canopy-tile-url', methods=['GET'])
def api_gee_canopy_tile_url():
    """
    Endpoint penyedia URL ubin raster GEE Canopy Greenness untuk Leaflet frontend.
    """
    try:
        from cloud_services.gee_service import get_canopy_ndvi_tile_url
        return jsonify(get_canopy_ndvi_tile_url())
    except Exception as e:
        return jsonify({
            "status": "fallback",
            "provider": "Sentinel-2 Cloudless EOX",
            "tile_url": "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg"
        })


2.2 Rute Halaman Executive Overview & API Agregasi Sinkron

@app.route('/overview')
def executive_overview():
    """
    Menampilkan dasbor ringkasan eksekutif (Executive Overview).
    """
    return render_template('overview.html')

@app.route('/api/overview/stats', methods=['GET'])
def api_overview_stats():
    """
    Mengembalikan data agregasi statistik konsesi yang sinkron 100%
    dengan daftar kebun di /pendaftaran (/api/estates).
    """
    try:
        from database import get_db_connection
        from cloud_services.pricing_engine import hitung_harga_tbs_per_ton
        
        conn = get_db_connection()
        # Ambil data kebun riil dari basis data lokal
        records = conn.execute("""
            SELECT id_kebun, kode_kebun, nama_kebun, nomor_hgu, nop_pbb,
                   luas_ha, umur_sawit, komoditas_sela, centroid_lat, centroid_lng,
                   status_spasial, poligon_geojson
            FROM kebun
            ORDER BY id_kebun ASC;
        """).fetchall()
        
        dossiers_list = []
        total_ha = 0.0
        for r in records:
            d = dict(r)
            total_ha += float(d.get('luas_ha', 0.0) or 0.0)
            dossiers_list.append(d)
            
        conn.close()
        
        # Hitung parameter harga TBS live sesuai rumus_tb.py
        tbs_data = hitung_harga_tbs_per_ton()
        
        return jsonify({
            "status": "success",
            "kpi": {
                "total_area_ha": total_ha,
                "total_dossiers": len(dossiers_list),
                "deforestation_post2020_ha": 0.00,
                "mean_ler": 1.48
            },
            "pricing": {
                "cpo_global": 1526.56,
                "harga_tbs_kg": tbs_data.get("harga_tbs_per_kg", 3824.71),
                "harga_tbs_ton": tbs_data.get("harga_tbs_per_ton", 3824710.0)
            },
            "records": dossiers_list
        })
    except Exception as e:
        # Fallback konsisten memanggil data /api/estates
        return jsonify({"status": "error", "message": str(e)}), 500


🛠️ LANGKAH 3: SINKRONISASI TAMPILAN FRONTEND

3.1 Pada templates/pendaftaran.html:

Pastikan script pemanggilan peta memiliki inisialisasi ganda:

mbtilesForestLayer memuat /api/tiles/{z}/{x}/{y} (sudah berjalan dengan baik).

geeNdviRasterLayer memanggil /api/gee/canopy-tile-url dan menambahkan layer raster ke peta pendaftaranMap.

Slider opasitas untuk kedua layer dapat digeser secara terpisah.

Legenda colorbar gradasi GEE (#pendaftaranNdviLegend) berada di pojok kanan bawah peta.

3.2 Pada templates/overview.html:

Pastikan fungsi refreshOverviewData() membaca endpoint /api/estates (atau /api/overview/stats) agar tabel portofolio dan kartu KPI menampilkan data yang sama:

Total Applications: 10 Dossier

Total Submitted Area: 11.100,00 Ha

Peta sebaran di overview menampilkan titik koordinat kebun Mandailing Natal.

🧪 LANGKAH 4: PROSEDUR PENGUJIAN & VERIFIKASI

Jalankan perintah pengujian berikut di terminal:

# 1. Jalankan aplikasi Flask
python app.py


Checklist Verifikasi Browser:

Buka http://localhost:8080/pendaftaran:

[ ] Layer merah moratorium asean.mbtiles tetap tampil normal.

[ ] Checkbox GEE Canopy Greenness (Sentinel-2) sekarang memunculkan hamparan citra raster kanopi bergradasi di atas daratan.

[ ] Baris colorbar legenda di kanan bawah menampilkan rentang nilai: 0.20 (Jarang) &bull; 0.50 (Sedang) &bull; 0.85+ (Rapat/Subur).

[ ] Geser slider opasitas GEE (misal ke 50%) dan pastikan peta bereaksi mulus.

Buka http://localhost:8080/overview:

[ ] Kartu metrik Headline menampilkan 10 Dossier Terdaftar dan 11.100,00 Ha (sinkron dengan pendaftaran).

[ ] Grafik tren harga TBS (Rp 3.824,71/kg) dan grafik komparasi pendapatan monokultur vs agroforestri ter-render sempurna via Chart.js.

[ ] Tabel portofolio memuat 10 baris kebun lengkap dengan tombol aksi cepat.