import os
from google.cloud import storage
from config import Config

BUCKET_NAME = Config.GCS_BUCKET
FILE_NAME = 'asean.mbtiles'
LOCAL_PATH = os.path.join(os.path.dirname(__file__), '..', 'static', 'data', FILE_NAME)

def ensure_mbtiles_available():
    """Memastikan berkas asean.mbtiles tersedia untuk Leaflet / Tile server."""
    os.makedirs(os.path.dirname(LOCAL_PATH), exist_ok=True)
    
    if os.path.exists(LOCAL_PATH) and os.path.getsize(LOCAL_PATH) > 0:
        print(f"[✓] MBTiles lokal sudah tersedia: {LOCAL_PATH}")
        return LOCAL_PATH

    print(f"[*] Mengunduh {FILE_NAME} dari GCS gs://{BUCKET_NAME}...")
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(FILE_NAME)
        if blob.exists():
            blob.download_to_filename(LOCAL_PATH)
            print(f"[+] Berhasil mengunduh MBTiles dari GCS ke {LOCAL_PATH}")
            return LOCAL_PATH
        else:
            print(f"[!] Warning: Blob {FILE_NAME} tidak ditemukan di bucket {BUCKET_NAME}")
            return None
    except Exception as e:
        print(f"[-] Gagal mengambil MBTiles dari GCS: {e}")
        return None

if __name__ == '__main__':
    ensure_mbtiles_available()
