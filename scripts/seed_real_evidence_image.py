import sqlite3
import base64
import hashlib
import os

DB_PATH = 'precision_palm.db'

def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    # Clean dummy test rows
    cur.execute("DELETE FROM inspection_evidence WHERE evidence_id LIKE 'EV-EST-MDN-001-2026-Q1-%'")

    # Load real image bytes from static/img/sawit_drone.jpg (or field_tm_weed.jpg)
    img_path = os.path.join('static', 'img', 'field_tm_weed.jpg')
    if not os.path.exists(img_path):
        img_path = os.path.join('static', 'img', 'sawit_drone.jpg')

    with open(img_path, 'rb') as f:
        img_bytes = f.read()

    b64_str = base64.b64encode(img_bytes).decode('utf-8')
    img_hash = hashlib.sha256(img_bytes).hexdigest()

    cur.execute("""
        UPDATE inspection_evidence 
        SET image_raw_base64 = ?,
            image_sha256_hash = ?,
            file_size_bytes = ?
        WHERE evidence_id = 'EV-MDN-2026-Q1'
    """, (b64_str, img_hash, len(img_bytes)))

    cur.execute("""
        INSERT OR REPLACE INTO used_photo_hashes (sha256_hash, evidence_id, dossier_id, company_id)
        VALUES (?, 'EV-MDN-2026-Q1', 'EST-MDN-001', 'COMP-MDN-001')
    """, (img_hash,))

    conn.commit()
    conn.close()
    print(f"Successfully seeded EV-MDN-2026-Q1 with {len(img_bytes)} bytes of real image ({img_path})")

if __name__ == '__main__':
    seed()
