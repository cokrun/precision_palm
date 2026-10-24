import sys
import types
import unittest
from unittest.mock import Mock, patch

import app as app_module


class FakeConnection:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.statements = []

    def execute(self, statement, params=()):
        self.statements.append((statement, params))
        if statement.lstrip().startswith("SELECT"):
            return FakeCursor({
                "evidence_id": "EV-TEST-1",
                "dossier_id": "EST-TEST",
                "image_sha256_hash": "a" * 64,
                "image_raw_base64": "encoded-image",
                "audit_year": 2026,
                "quarter_cycle": "Q1",
                "company_name": "Test Estate",
                "weather_satellite_validation": None,
            })
        return FakeCursor()

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        pass


class FakeCursor:
    def __init__(self, row=None):
        self.row = row
        self.rowcount = 1

    def fetchone(self):
        return self.row


class TestSpatialScanPersistence(unittest.TestCase):
    def test_local_scan_is_saved_when_bigquery_sync_raises(self):
        connection = FakeConnection()
        bigquery_module = types.ModuleType("cloud_services.bigquery_audit")
        bigquery_module.sync_evidence_to_bigquery = Mock(side_effect=RuntimeError("BigQuery unavailable"))
        scan_result = {
            "physical_entities": [{"label": "palm crown"}],
            "diagnostic_matrix_44": {},
        }

        with patch.object(app_module, "get_pure_db_connection", return_value=connection), patch.dict(
            sys.modules,
            {"cloud_services.bigquery_audit": bigquery_module},
        ):
            result = app_module.update_server_with_latest_scan(
                scan_result,
                filename="evidence.jpg",
                evidence_id="EV-TEST-1",
                image_sha256="a" * 64,
            )

        self.assertTrue(result["saved"])
        self.assertEqual(result["sync_status"], "LOCAL_ONLY")
        self.assertIn("tersimpan lokal", result["message"])
        self.assertGreaterEqual(connection.commits, 1)
        self.assertEqual(connection.rollbacks, 0)
        bigquery_module.sync_evidence_to_bigquery.assert_called_once()


if __name__ == "__main__":
    unittest.main()
