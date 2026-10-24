import unittest
from unittest.mock import patch

import app as app_module


class FakeCursor:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, evidence=None, surveillance=None):
        self.evidence = evidence
        self.surveillance = surveillance
        self.statements = []
        self.commits = 0

    def execute(self, statement, params=()):
        self.statements.append((statement, params))
        if statement.lstrip().startswith("SELECT") and "FROM inspection_evidence" in statement:
            return FakeCursor(self.evidence)
        if statement.lstrip().startswith("SELECT") and "FROM field_surveillance_records" in statement:
            return FakeCursor(self.surveillance)
        return FakeCursor()

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass

    def close(self):
        pass


class TestSpatialUnseal(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def test_unseals_evidence_using_photo_url_when_id_does_not_match(self):
        connection = FakeConnection(evidence={
            "evidence_id": "EV-TEST-1",
            "id": "EV-TEST-1",
            "dossier_id": "EST-TEST",
            "detected_entities_json": "[]",
        })
        with patch.object(app_module, "get_pure_db_connection", return_value=connection):
            response = self.client.post("/api/spatial/unseal-photo", json={
                "evidence_id": "legacy-gallery-id",
                "photo_url": "/api/media/evidence/EV-TEST-1",
            })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["evidence_id"], "EV-TEST-1")
        self.assertEqual(response.get_json()["is_locked"], False)
        self.assertEqual(connection.commits, 1)

    def test_unseals_orphaned_surveillance_record_instead_of_404(self):
        connection = FakeConnection(surveillance={
            "record_id": "SURV-TEST-1",
            "dossier_id": "EST-TEST",
            "evidence_id": "",
            "foto_url": "/static/evidence/legacy.jpg",
        })
        with patch.object(app_module, "get_pure_db_connection", return_value=connection):
            response = self.client.post("/api/spatial/unseal-photo", json={
                "evidence_id": "SURV-TEST-1",
                "photo_url": "/static/evidence/legacy.jpg",
            })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["surveillance_link_removed"])
        self.assertEqual(connection.commits, 1)
        self.assertTrue(any("DELETE FROM field_surveillance_records" in sql for sql, _ in connection.statements))


if __name__ == "__main__":
    unittest.main()
