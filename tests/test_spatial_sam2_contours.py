import base64
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import cv2
import numpy as np

import app as app_module
from cloud_services.image_contour import (
    build_opencv_static_replay_preview,
    build_sam2_contour_preview,
)


class TestSam2ContourPreview(unittest.TestCase):
    def make_image_bytes(self, width=300, height=200):
        image = np.zeros((height, width, 3), dtype=np.uint8)
        cv2.rectangle(image, (80, 50), (220, 160), (255, 255, 255), thickness=-1)
        success, encoded = cv2.imencode(".png", image)
        self.assertTrue(success)
        return encoded.tobytes()

    def make_model(self, mask):
        model = Mock()
        model.predict.return_value = [
            SimpleNamespace(masks=SimpleNamespace(data=np.asarray([mask], dtype=np.uint8)))
        ]
        return model

    def test_opencv_static_replay_returns_diagnostic_contour(self):
        image = np.zeros((200, 300, 3), dtype=np.uint8)
        cv2.rectangle(image, (40, 30), (260, 170), (0, 180, 0), thickness=-1)
        success, encoded = cv2.imencode(".png", image)
        self.assertTrue(success)

        result = build_opencv_static_replay_preview(encoded.tobytes(), replay_frames=30)

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["method"], "opencv_hsv_ema_static_replay")
        self.assertEqual(result["verification"], "diagnostic_static_replay_not_streaming")
        self.assertEqual(result["replay_frames"], 30)
        self.assertEqual(result["first_locked_frame"], 1)
        self.assertGreater(result["mask_coverage_percent"], 50)
        self.assertEqual(len(result["contours"]), 1)
        self.assertEqual(result["contours"][0]["bbox_xywh"], [40, 30, 221, 141])
        overlay_bytes = base64.b64decode(result["mask_overlay_base64"])
        overlay = cv2.imdecode(np.frombuffer(overlay_bytes, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.assertEqual(overlay.shape, (200, 300, 4))
        self.assertGreater(cv2.countNonZero(overlay[:, :, 3]), 0)
        self.assertEqual(int(overlay[:, :, 3].max()), 28)

    def test_opencv_static_replay_rejects_invalid_frame_count(self):
        result = build_opencv_static_replay_preview(self.make_image_bytes(), replay_frames=0)

        self.assertEqual(
            result,
            {"status": "unavailable", "reason": "invalid_replay_frame_count"},
        )

    def test_box_prompt_generates_contour_from_sam_mask(self):
        mask = np.zeros((200, 300), dtype=np.uint8)
        cv2.rectangle(mask, (80, 50), (220, 160), 1, thickness=-1)
        model = self.make_model(mask)

        with patch("cloud_services.image_contour._load_sam_model", return_value=model):
            result = build_sam2_contour_preview(
                self.make_image_bytes(),
                [{
                    "box_2d": [200, 250, 800, 750],
                    "label_name": "Palm canopy",
                    "cluster": "palm_canopy",
                }],
                model_path="sam2.1_b.pt",
            )

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["method"], "sam2_box_prompt_opencv_contour")
        self.assertEqual(result["verification"], "unverified_model_segmentation")
        self.assertEqual((result["width"], result["height"]), (300, 200))
        self.assertEqual(result["coordinate_space"], "original_image_pixels")
        self.assertEqual(len(result["contours"]), 1)
        self.assertEqual(result["contours"][0]["entity_index"], 0)
        self.assertEqual(result["contours"][0]["label"], "Palm canopy")
        self.assertEqual(result["contours"][0]["cluster"], "palm_canopy")
        self.assertGreaterEqual(result["contours"][0]["edge_support"], 0)
        points = result["contours"][0]["points"]
        self.assertGreaterEqual(len(points), 3)
        self.assertTrue(all(70 <= x <= 230 and 35 <= y <= 165 for x, y in points))
        model.predict.assert_called_once()
        self.assertEqual(
            model.predict.call_args.kwargs["bboxes"],
            [[75.0, 40.0, 225.0, 160.0]],
        )

    def test_resizing_preserves_original_image_coordinates(self):
        mask = np.zeros((800, 1600), dtype=np.uint8)
        cv2.rectangle(mask, (620, 220), (980, 580), 1, thickness=-1)
        model = self.make_model(mask)

        with patch("cloud_services.image_contour._load_sam_model", return_value=model):
            result = build_sam2_contour_preview(
                self.make_image_bytes(width=2400, height=1200),
                [{"box_2d": [250, 375, 750, 625]}],
            )

        self.assertEqual(result["status"], "ready")
        self.assertEqual((result["width"], result["height"]), (2400, 1200))
        points = result["contours"][0]["points"]
        self.assertTrue(all(850 <= x <= 1550 and 250 <= y <= 950 for x, y in points))

    def test_ignores_invalid_detection_boxes(self):
        model = Mock()
        with patch("cloud_services.image_contour._load_sam_model", return_value=model):
            result = build_sam2_contour_preview(
                self.make_image_bytes(),
                [
                    {"box_2d": [0, 0, 1001, 500]},
                    {"box_2d": ["bad", 0, 100, 100]},
                    {"box_2d": [300, 400, 200, 500]},
                ],
            )

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["contours"], [])
        model.predict.assert_not_called()

    def test_reports_invalid_image_without_throwing(self):
        for image_bytes in (b"", b"not an image"):
            with self.subTest(image_bytes=image_bytes):
                result = build_sam2_contour_preview(image_bytes, [])
                self.assertEqual(
                    result,
                    {"status": "unavailable", "reason": "image_decode_failed"},
                )

    def test_missing_checkpoint_is_explicit(self):
        with patch(
            "cloud_services.image_contour._load_sam_model",
            side_effect=FileNotFoundError("checkpoint missing"),
        ):
            result = build_sam2_contour_preview(
                self.make_image_bytes(),
                [{"box_2d": [200, 250, 800, 750]}],
            )

        self.assertEqual(
            result,
            {"status": "unavailable", "reason": "sam2_checkpoint_missing"},
        )

    def test_saved_contour_endpoint_reuses_saved_detections(self):
        connection = Mock()
        connection.execute.return_value.fetchone.return_value = {
            "evidence_id": "EV-TEST-1",
            "image_raw_base64": base64.b64encode(self.make_image_bytes()).decode("ascii"),
            "detected_entities_json": json.dumps([{"box_2d": [200, 250, 800, 750]}]),
            "is_processed": 1,
        }
        app_module.app.config["TESTING"] = True
        client = app_module.app.test_client()
        preview = {"status": "ready", "method": "sam2_box_prompt_opencv_contour", "contours": []}

        with (
            patch.object(app_module, "get_pure_db_connection", return_value=connection),
            patch.dict("os.environ", {"SPATIAL_SAM2_ENABLED": "1"}),
            patch("cloud_services.image_contour.build_sam2_contour_preview", return_value=preview) as run_sam,
        ):
            response = client.post(
                "/api/spatial/contour-preview",
                json={"evidence_id": "EV-TEST-1"},
            )

        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["contour_preview"], preview)
        self.assertEqual(connection.execute.call_count, 1)
        run_sam.assert_called_once()

    def test_endpoint_is_disabled_by_default(self):
        app_module.app.config["TESTING"] = True
        client = app_module.app.test_client()

        with patch.dict("os.environ", {}, clear=True):
            response = client.post(
                "/api/spatial/contour-preview",
                json={"evidence_id": "EV-TEST-1"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["contour_preview"]["reason"],
            "sam2_disabled",
        )

    def test_endpoint_rejects_missing_evidence_id(self):
        app_module.app.config["TESTING"] = True
        client = app_module.app.test_client()

        with patch.dict("os.environ", {"SPATIAL_SAM2_ENABLED": "1"}):
            response = client.post("/api/spatial/contour-preview", json={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["status"], "error")

    def test_opencv_static_replay_endpoint_reads_evidence_without_writing(self):
        connection = Mock()
        connection.execute.return_value.fetchone.return_value = {
            "image_raw_base64": base64.b64encode(self.make_image_bytes()).decode("ascii"),
        }
        app_module.app.config["TESTING"] = True
        client = app_module.app.test_client()
        preview = {
            "status": "ready",
            "method": "opencv_hsv_ema_static_replay",
            "verification": "diagnostic_static_replay_not_streaming",
            "contours": [],
        }

        with (
            patch.object(app_module, "get_pure_db_connection", return_value=connection),
            patch("cloud_services.image_contour.build_opencv_static_replay_preview", return_value=preview) as run_replay,
        ):
            response = client.post(
                "/api/spatial/opencv-static-replay",
                json={"evidence_id": "EV-TEST-1"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["replay_preview"], preview)
        connection.execute.assert_called_once()
        run_replay.assert_called_once()


if __name__ == "__main__":
    unittest.main()
