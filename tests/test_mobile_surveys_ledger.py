import unittest
import sqlite3
from unittest.mock import patch

import app as server


class _Cursor:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, _query, _params):
        return self

    def fetchall(self):
        return self.rows


class _Connection:
    def __init__(self, rows):
        self.rows = rows

    def cursor(self):
        return _Cursor(self.rows)

    def close(self):
        pass


class _WriteConnection:
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE kebun_profil (id_kebun INTEGER, kode_kebun TEXT);
            CREATE TABLE kebun_monitoring_log (
                id_log INTEGER PRIMARY KEY AUTOINCREMENT,
                id_kebun INTEGER, periode_siklus TEXT, tahun_siklus INTEGER, titik_ke INTEGER,
                gps_lat REAL, gps_lng REAL, elevasi_dpl REAL, ketinggian_agl REAL,
                kemiringan_lereng REAL, view_perspective TEXT, foto_url TEXT,
                waktu_pengambilan TEXT, cuaca_tercatat TEXT, cuaca_satellite_match INTEGER,
                piringan_steril_meter REAL, defisit_tbs_persen REAL, ai_scan_status TEXT,
                ai_scan_result_json TEXT, sha256_seal TEXT, kode_kebun TEXT, mandor TEXT, blok TEXT
            );
        """)

    def execute(self, *args):
        return self.db.execute(*args)

    def cursor(self):
        return self.db.cursor()

    def commit(self):
        self.db.commit()

    def close(self):
        pass


class _PureConnection:
    def execute(self, _query, _params=()):
        return self

    def fetchone(self):
        return None

    def commit(self):
        pass

    def close(self):
        pass


class TestMobileSurveysLedger(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()

    def test_local_report_is_returned_when_database_is_unavailable(self):
        local_reports = [
            {
                "id_log": 9001,
                "kode_kebun": "EST-TEST-001",
                "periode_siklus": "Q2",
                "tahun_siklus": 2026,
                "titik_ke": 4,
                "foto_url": "/api/media/evidence/EV-TEST-001",
                "bounding_boxes": [{"label": "palm canopy"}],
                "ai_scan_status": "LIVE_GEMINI"
            },
            {
                "id_log": 9002,
                "kode_kebun": "EST-OTHER-001",
                "periode_siklus": "Q2",
                "tahun_siklus": 2026,
                "titik_ke": 4
            }
        ]
        with patch.object(server, "get_db", side_effect=RuntimeError("database unavailable")), \
                patch.object(server, "read_local_store", return_value={"field_tracking": local_reports}):
            response = self.client.get("/api/mobile-surveys?kode=EST-TEST-001")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["total"], 1)
        report = payload["data"][0]
        self.assertEqual(report["kode_kebun"], "EST-TEST-001")
        self.assertEqual(report["foto_url"], "/api/media/evidence/EV-TEST-001")
        self.assertEqual(report["bounding_boxes"], [{"label": "palm canopy"}])
        self.assertEqual(report["ai_scan_status"], "LIVE_GEMINI")
        self.assertEqual(report["source"], "local")
        self.assertIn("warning", payload)

    def test_local_report_refreshes_matching_database_ledger_row(self):
        database_row = {
            "id": 41,
            "id_log": 41,
            "id_kebun": 7,
            "kode_kebun": "EST-TEST-001",
            "nama_kebun": "Test Estate",
            "periode_siklus": "Q2",
            "tahun_siklus": 2026,
            "titik_ke": 4,
            "blok": "Old block",
            "mandor": "Old foreman",
            "timestamp": "2026-10-01 10:00 WIB",
            "waktu_pengambilan": "2026-10-01 10:00",
            "latitude": 0.8,
            "longitude": 99.5,
            "elevasi": 140,
            "slope": 4.5,
            "foto_url": "/static/img/old-photo.jpg",
            "piringan_steril_meter": 2.0,
            "defisit_tbs_persen": 1.2,
            "cuaca": "Cerah",
            "ai_scan_status": "not_scanned",
            "ai_scan_result_json": None,
            "sha256_seal": "old-seal"
        }
        local_report = {
            "id_log": 9001,
            "id_kebun": 7,
            "kode_kebun": "EST-TEST-001",
            "periode_siklus": "Q2",
            "tahun_siklus": 2026,
            "titik_ke": 4,
            "blok": "Updated block",
            "mandor": "Updated foreman",
            "foto_url": "/api/media/evidence/EV-TEST-001",
            "bounding_boxes": [{"label": "palm canopy"}],
            "ai_scan_status": "LIVE_GEMINI"
        }
        with patch.object(server, "get_db", return_value=_Connection([database_row])), \
                patch.object(server, "read_local_store", return_value={"field_tracking": [local_report]}):
            response = self.client.get("/api/mobile-surveys?kode=EST-TEST-001")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["total"], 1)
        report = payload["data"][0]
        self.assertEqual(report["id"], 41)
        self.assertEqual(report["id_log"], 41)
        self.assertEqual(report["foto_url"], "/api/media/evidence/EV-TEST-001")
        self.assertEqual(report["blok"], "Updated block")
        self.assertEqual(report["mandor"], "Updated foreman")
        self.assertEqual(report["bounding_boxes"], [{"label": "palm canopy"}])
        self.assertEqual(report["source"], "database+local")

    def test_post_persists_selected_photo_and_vision_results(self):
        stored = {"field_tracking": [], "estates": []}
        payload = {
            "kode_kebun": "EST-TEST-001",
            "periode_siklus": "Q3",
            "tahun_siklus": 2026,
            "titik_ke": 6,
            "foto_url": "data:image/jpeg;base64,YWJj",
            "photos": ["data:image/jpeg;base64,YWJj"],
            "ai_scan_status": "LIVE_GEMINI",
            "bounding_boxes": [{"label": "palm canopy", "confidence": 0.91}],
            "plant_diagnostics": {"health": "observed"},
            "ai_scan_result": {"status": "success", "mode": "LIVE_GEMINI"}
        }
        with patch.object(server, "get_db", return_value=_WriteConnection()), \
                patch.object(server, "get_pure_db_connection", return_value=_PureConnection()), \
                patch.object(server, "read_local_store", return_value=stored), \
                patch.object(server, "save_local_store"), \
                patch.object(server, "send_monitoring_log_to_bigquery_async"), \
                patch("cloud_services.bigquery_audit.sync_evidence_to_bigquery_async"):
            response = self.client.post("/api/mobile-surveys", json=payload)

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        saved = response.get_json()["data"]
        self.assertEqual(saved["foto_url"], payload["foto_url"])
        self.assertEqual(saved["photos"], payload["photos"])
        self.assertEqual(saved["ai_scan_status"], "LIVE_GEMINI")
        self.assertEqual(saved["bounding_boxes"], payload["bounding_boxes"])
        self.assertIn("evidence_id", saved)


if __name__ == "__main__":
    unittest.main()
