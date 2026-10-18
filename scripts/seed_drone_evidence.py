import sqlite3
import os
import base64
import hashlib
import json

conn = sqlite3.connect('precision_palm.db')
cur = conn.cursor()
r = cur.execute("SELECT evidence_id FROM inspection_evidence WHERE evidence_id = 'EV-MDN-2026-Q1-DRONE'").fetchone()
if not r:
    drone_path = os.path.join('static', 'img', 'sawit_drone.jpg')
    with open(drone_path, 'rb') as f:
        raw = f.read()
    h = hashlib.sha256(raw).hexdigest()
    b64 = base64.b64encode(raw).decode('utf-8')
    entities = json.dumps([
        {"label": "Canopy Crown Ortho", "box_2d": [180, 120, 820, 880], "cluster": "palm_canopy", "confidence": 0.98},
        {"label": "45m UAV Flight Corridor", "box_2d": [310, 220, 740, 790], "cluster": "alley_corridor", "confidence": 0.96}
    ])
    cur.execute("""
        INSERT OR REPLACE INTO inspection_evidence (
            evidence_id, dossier_id, mandor_id, audit_year, quarter_cycle, perspective_mode,
            altitude_agl_m, camera_pitch_degrees, latitude_exif, longitude_exif,
            image_raw_base64, image_sha256_hash, file_size_bytes, ai_vision_model,
            detected_entities_json, chlorophyll_spad_inferred, root_clearance_verified_m,
            weather_satellite_validation
        ) VALUES (
            'EV-MDN-2026-Q1-DRONE', 'EST-MDN-001', 'MDR-MDN-01', 2026, 'Q1', 'AERIAL_DRONE',
            45.0, -90.0, 0.824100, 99.561200,
            ?, ?, ?, 'gemini-3.8-flash',
            ?, 82.4, 2.05, 'MATCH_SUNNY_PRECIPITATION_0MM'
        );
    """, (b64, h, len(raw), entities))
    cur.execute("INSERT OR IGNORE INTO used_photo_hashes (sha256_hash, evidence_id, dossier_id, company_id) VALUES (?, 'EV-MDN-2026-Q1-DRONE', 'EST-MDN-001', 'COMP-MDN-001')", (h,))
    conn.commit()
    print('Inserted EV-MDN-2026-Q1-DRONE successfully!')
else:
    print('EV-MDN-2026-Q1-DRONE already exists.')
conn.close()
