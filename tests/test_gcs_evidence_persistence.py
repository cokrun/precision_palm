import unittest
from unittest.mock import patch

import cv2
import numpy as np

import app as app_module


class FakeCursor:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows or []

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class FakeMediaConnection:
    def execute(self, statement, params=()):
        if statement.lstrip().startswith("PRAGMA"):
            return FakeCursor(rows=[
                (0, "evidence_id"),
                (1, "id"),
                (2, "image_raw_base64"),
                (3, "image_base64"),
                (4, "image_mime_type"),
                (5, "uploaded_at"),
            ])
        return FakeCursor()

    def close(self):
        pass


class TestGcsEvidencePersistence(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def test_evidence_upload_writes_image_and_manifest_to_shared_storage(self):
        with patch.object(app_module, "_running_on_managed_cloud", return_value=True), patch(
            "cloud_services.bigquery_manager.upload_file_to_gcs",
            side_effect=["gs://bucket/media", "gs://bucket/manifest", "gs://bucket/index"],
        ) as upload:
            stored = app_module._store_evidence_in_gcs(
                "EV-TEST-1",
                "EST-TEST",
                b"image-bytes",
                "image/jpeg",
                {"audit_year": 2026, "quarter_cycle": "Q1"},
            )

        self.assertEqual(stored["gcs_uri"], "gs://bucket/media")
        self.assertEqual(upload.call_count, 3)
        self.assertEqual(upload.call_args_list[0].args[0], b"image-bytes")
        self.assertIn("/metadata/", upload.call_args_list[1].args[1])
        self.assertEqual(upload.call_args_list[1].kwargs["content_type"], "application/json")

    def test_shared_evidence_is_appended_for_gallery_consumers(self):
        photos = []
        manifest = {
            "evidence_id": "EV-TEST-1",
            "dossier_id": "EST-TEST-2026",
            "audit_year": 2026,
            "quarter_cycle": "Q1",
            "perspective_mode": "AERIAL_DRONE",
            "media_object": "inspection_evidence/media/test",
            "detected_entities_json": "[]",
        }
        with patch.object(app_module, "_load_shared_evidence", return_value=[manifest]):
            app_module._append_shared_evidence(photos, "EST-TEST", 2026)

        self.assertEqual(len(photos), 1)
        self.assertEqual(photos[0]["evidence_id"], "EV-TEST-1")
        self.assertEqual(photos[0]["file_url"], "/api/media/evidence/EV-TEST-1")

    def test_managed_cloud_rejects_upload_when_gcs_does_not_persist_image(self):
        with patch.object(app_module, "_running_on_managed_cloud", return_value=True), patch(
            "cloud_services.bigquery_manager.upload_file_to_gcs",
            return_value=None,
        ):
            with self.assertRaisesRegex(RuntimeError, "GCS image upload failed"):
                app_module._store_evidence_in_gcs(
                    "EV-TEST-2",
                    "EST-TEST",
                    b"image-bytes",
                    "image/jpeg",
                    {"audit_year": 2026},
                )

    def test_direct_upload_returns_error_when_gcs_manifest_upload_fails(self):
        with patch.object(app_module, "_running_on_managed_cloud", return_value=True), patch.object(
            app_module, "is_photo_hash_reused", return_value=False
        ), patch.object(app_module, "get_pure_db_connection") as db_connection, patch(
            "cloud_services.bigquery_manager.upload_file_to_gcs",
            side_effect=["gs://bucket/media", None],
        ), patch(
            "cloud_services.bigquery_manager.delete_gcs_blob"
        ) as delete_blob:
            response = self.client.post(
                "/api/spatial/upload-photo-direct",
                json={
                    "dossier_id": "EST-TEST",
                    "image_base64": "data:image/jpeg;base64,aW1hZ2U=",
                },
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["status"], "error")
        self.assertIn("metadata upload failed", response.get_json()["message"])
        db_connection.assert_not_called()
        delete_blob.assert_called_once()

    def test_media_endpoint_streams_from_gcs_when_instance_sqlite_has_no_record(self):
        with patch.object(app_module, "get_pure_db_connection", return_value=FakeMediaConnection()), patch(
            "cloud_services.bigquery_manager.download_file_from_gcs",
            return_value=(b"shared-image-bytes", "image/jpeg"),
        ) as download:
            response = self.client.get("/api/media/evidence/EV-TEST-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"shared-image-bytes")
        self.assertEqual(response.mimetype, "image/jpeg")
        download.assert_called_once()

    def test_shared_image_reader_resolves_index_and_media_objects(self):
        evidence_id = "EV-SCAN-1"
        manifest = {
            "evidence_id": evidence_id,
            "filename": "scan.png",
            "media_object": "inspection_evidence/media/scan",
            "image_mime_type": "image/png",
        }

        def download(object_name):
            if object_name == app_module._evidence_index_object_name(evidence_id):
                import json
                return json.dumps(manifest).encode("utf-8"), "application/json"
            if object_name == manifest["media_object"]:
                return b"shared-image-bytes", "image/jpeg"
            return None

        with patch(
            "cloud_services.bigquery_manager.download_file_from_gcs",
            side_effect=download,
        ):
            result = app_module._read_shared_evidence_image(evidence_id=evidence_id)

        self.assertEqual(result, (b"shared-image-bytes", "image/png", manifest))

    def test_scan_image_uses_shared_gcs_image_when_instance_database_is_empty(self):
        evidence_id = "EV-SCAN-2"
        shared_record = {
            "evidence_id": evidence_id,
            "filename": "field-scan.png",
        }
        live_result = {
            "api_telemetry": {
                "is_live_gemini_called": True,
                "api_call_status": "LIVE_GOOGLE_CLOUD_SUCCESS",
                "model_invoked": "gemini-test",
            },
            "physical_entities": [],
            "detected_objects": [],
        }

        with patch.object(
            app_module, "get_pure_db_connection", return_value=FakeMediaConnection()
        ), patch.object(
            app_module,
            "_read_shared_evidence_image",
            return_value=(b"shared-image-bytes", "image/png", shared_record),
        ), patch(
            "cloud_services.grounded_auditor.audit_image_with_gemini",
            return_value=live_result,
        ) as audit_image, patch(
            "cloud_services.agentic_vision_supervisor.FieldVisionSupervisorAgent.evaluate_and_supervise",
            side_effect=lambda raw_analysis, **kwargs: raw_analysis,
        ), patch.object(
            app_module, "update_server_with_latest_scan", return_value={"saved": True}
        ):
            response = self.client.post(
                "/api/ai/scan-image",
                json={
                    "evidence_id": evidence_id,
                    "image_url": f"/api/media/evidence/{evidence_id}",
                    "dossier_id": "EST-SCAN-2026",
                    "filename": "field-scan.png",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["mode"], "LIVE_GEMINI")
        self.assertEqual(audit_image.call_args.kwargs["image_bytes"], b"shared-image-bytes")
        self.assertEqual(audit_image.call_args.kwargs["mime_type"], "image/png")

    def test_opencv_replay_uses_shared_gcs_image_when_instance_database_is_empty(self):
        image = np.zeros((160, 200, 3), dtype=np.uint8)
        cv2.rectangle(image, (20, 20), (180, 140), (0, 180, 0), thickness=-1)
        encoded, image_png = cv2.imencode(".png", image)
        self.assertTrue(encoded)

        with patch.object(
            app_module, "get_pure_db_connection", return_value=FakeMediaConnection()
        ), patch.object(
            app_module,
            "_read_shared_evidence_image",
            return_value=(image_png.tobytes(), "image/png", {"evidence_id": "EV-CV-1"}),
        ):
            response = self.client.post(
                "/api/spatial/opencv-static-replay",
                json={"evidence_id": "EV-CV-1"},
            )

        self.assertEqual(response.status_code, 200)
        preview = response.get_json()["replay_preview"]
        self.assertEqual(preview["status"], "ready")
        self.assertEqual(preview["method"], "opencv_hsv_ema_static_replay")
        self.assertGreater(len(preview["contours"]), 0)


if __name__ == "__main__":
    unittest.main()
