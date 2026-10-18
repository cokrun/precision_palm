# cloud_services/tile_server.py
import sqlite3
import os
from flask import Blueprint, make_response
from cloud_services.gcs_spatial import ensure_mbtiles_available

tiles_bp = Blueprint('tiles_bp', __name__)
MBTILES_PATH = os.path.join(os.path.dirname(__file__), '..', 'static', 'data', 'asean.mbtiles')

EMPTY_PNG = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

def make_png_response(data):
    resp = make_response(data)
    resp.headers.set('Content-Type', 'image/png')
    resp.headers.set('Content-Length', str(len(data)))
    resp.headers.set('Access-Control-Allow-Origin', '*')
    resp.headers.set('Cache-Control', 'public, max-age=86400')
    return resp

@tiles_bp.route('/api/tiles/<int:z>/<int:x>/<int:y>')
@tiles_bp.route('/api/tiles/<int:z>/<int:x>/<int:y>.png')
@tiles_bp.route('/tiles/<int:z>/<int:x>/<int:y>')
@tiles_bp.route('/tiles/<int:z>/<int:x>/<int:y>.png')
def get_tile(z, x, y):
    if not os.path.exists(MBTILES_PATH):
        ensure_mbtiles_available()

    if not os.path.exists(MBTILES_PATH):
        return make_png_response(EMPTY_PNG)

    tms_y = (1 << z) - 1 - y

    try:
        conn = sqlite3.connect(f"file:{MBTILES_PATH}?mode=ro", uri=True)
        cursor = conn.cursor()

        # Prioritas 1: Kueri skema TMS standar
        cursor.execute("SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?", (z, x, tms_y))
        row = cursor.fetchone()

        # Prioritas 2: Kueri skema XYZ langsung
        if not row or not row[0]:
            cursor.execute("SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?", (z, x, y))
            row = cursor.fetchone()

        conn.close()

        if row and row[0]:
            tile_bytes = row[0]
            # Jika merupakan data PNG yang valid
            if tile_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                return make_png_response(tile_bytes)

        return make_png_response(EMPTY_PNG)

    except Exception as e:
        print(f"Error serving tile {z}/{x}/{y}: {e}")
        return make_png_response(EMPTY_PNG)
