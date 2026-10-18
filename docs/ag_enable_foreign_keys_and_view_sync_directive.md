# DIRECTIVE RESMI AG: AKTIFKAN FOREIGN KEYS PRAGMA & SINKRONKAN VIEW TIMELINES/SPATIAL KE DATABASE MURNI

**Status:** Penyempurnaan Akhir Backend & View (Final Polish Directive)  
**Tujuan:** Mengaktifkan Foreign Keys SQLite di setiap koneksi dan memastikan data bersih dari `test_db_cli.py` ter-render sempurna di `timelines.html` dan `spatial.js`.

---

## 1. AKTIFKAN FOREIGN KEYS DI `database_schema_engine.py` & `database.py`

Pada fungsi pembuka koneksi `get_db_connection()`, pastikan baris PRAGMA berikut dieksekusi:

```python
# STREAMING_CHUNK:Enforcing Foreign Key constraint in SQLite connection
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")  # <-- WAJIB DIPASTIKAN AKTIF
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

2. SINKRONISASI VIEW PADA timelines.html & spatial.js

Hasil tes CLI membuktikan bahwa dossier seperti EST-RIAU-002 berstatus EMPTY STATE VALID.

Maka di file JavaScript frontend (timelines.js dan spatial.js):

    Saat latest_evidence kosong (null):

        Tampilkan wadah kosong bertuliskan:

        "Belum ada foto inspeksi lapangan untuk berkas ini. Silakan lakukan pengambilan foto melalui modul Mobile PWA."

        Bersihkan canvas/SVG overlay:

        document.getElementById('aiReticleSvgOverlay').innerHTML = '';

        Jangan merender 16 kotak bounding box di atas kotak kosong.

    Saat latest_evidence ada data (seperti pada EST-MDN-001):

        Render gambar dari URL: latest_evidence.media_stream_url (/api/media/evidence/<id>).

        Render bounding box SVG dinamis dari properti detected_entities_json yang tersimpan di baris database tersebut.