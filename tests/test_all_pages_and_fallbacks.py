#!/usr/bin/env python3
"""
Comprehensive Test Suite for Precision Palm Cloud
Tests all Pages, AI APIs, Governance Config, and Autonomous Statutory Fallbacks.
"""

import os
import sys
import json
import sqlite3
import tempfile
import unittest
import uuid
from io import BytesIO
from unittest.mock import Mock, patch

# Set testing environment
os.environ["FLASK_ENV"] = "testing"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, get_pure_db_connection

class TestAllPagesAndFallbacks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        cls.client = app.test_client()

    # =========================================================================
    # 1. TEST ALL WEB PAGES
    # =========================================================================
    def test_01_page_home(self):
        """Test GET / (Overview Dashboard)"""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Precision Palm", res.data)

    def test_02_page_spatial(self):
        """Test GET /spatial (Stage 1: Spatial GIS)"""
        res = self.client.get('/spatial', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"spatial", res.data.lower())

    def test_03_page_verifikasi(self):
        """Test GET /verifikasi (Stage 2A: Verification)"""
        res = self.client.get('/verifikasi')
        self.assertEqual(res.status_code, 200)

    def test_04_page_validasi(self):
        """Test GET /validasi (Stage 2A Validation)"""
        res = self.client.get('/validasi')
        self.assertEqual(res.status_code, 200)

    def test_05_page_simulator(self):
        """Test GET /simulator (Stage 2B In-Silico Simulator)"""
        res = self.client.get('/simulator', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        # Verify theme, zone 2 dossier, and passport button markup
        self.assertIn(b"zona_2_biophysical_dossier", res.data)
        self.assertIn(b"btnQuickPassport", res.data)
        self.assertIn(b"simContourProgress", res.data)
        self.assertIn(b"simContourOverlay", res.data)
        self.assertIn(b"hybrid_contour_preview.js", res.data)

    def test_06_page_timelines(self):
        """Test GET /timelines (Stage 3: Surveillance Tracking)"""
        res = self.client.get('/timelines', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"timelineContourProgress", res.data)
        self.assertIn(b"timelineContourOverlay", res.data)
        self.assertIn(b"setTimelineEvidenceContext", res.data)

    def test_07_page_certificate(self):
        """Test GET /certificate/1 (EcoGreen Digital Passport)"""
        res = self.client.get('/certificate/1')
        self.assertEqual(res.status_code, 200)

    def test_08_page_mobile(self):
        """Test GET /mobile (Foreman Mandor Field PWA)"""
        res = self.client.get('/mobile')
        self.assertEqual(res.status_code, 200)

    def test_09_page_ai_logs(self):
        """Test GET /ai-logs (AI Audit & Governance Logs)"""
        res = self.client.get('/ai-logs')
        self.assertEqual(res.status_code, 200)

    def test_10_page_pengaturan(self):
        """Test GET /pengaturan (Governance Settings)"""
        res = self.client.get('/pengaturan', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

    # =========================================================================
    # 2. TEST ENVIRONMENT CONFIGURATION GOVERNANCE (ZERO SECRETS)
    # =========================================================================
    def test_11_api_config_security(self):
        """Test GET /api/config ensures zero API key leakage"""
        res = self.client.get('/api/config')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        cfg = data.get("config", {})
        
        # Verify GEMINI_API_KEY is NOT exposed
        self.assertNotIn("GEMINI_API_KEY", cfg)
        self.assertNotIn("api_key", cfg)
        # Verify public configs are exposed
        self.assertIn("gcp_project", cfg)
        self.assertIn("gcp_region", cfg)
        self.assertIn("gcs_spatial_bucket", cfg)
        self.assertIn("app_base_url", cfg)

    # =========================================================================
    # 3. TEST FINANCIAL & TBS PRICING ENGINE
    # =========================================================================
    def test_12_api_pricing_tbs(self):
        """Pricing cannot be calculated from unrelated crop-yield query inputs."""
        res = self.client.get('/api/pricing/tbs-calculation?palm_yield_ton_ha=24.0&intercrop_yield_ton_ha=7.5&intercrop_price_idr_kg=18500.0')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "unavailable")
        self.assertGreater(len(data.get("missing_fields", [])), 0)
        self.assertNotIn("data", data)

    # =========================================================================
    # 4. TEST AGROECOLOGICAL REASONING API & FALLBACK ENGINE
    # =========================================================================
    def test_13_crop_reasoning_live_or_fallback(self):
        """Test POST /api/ai/crop-reasoning standard execution"""
        payload = {
            "palm_age": 6.0,
            "crops": ["Jahe Merah (Zingiber officinale var. rubrum)"],
            "soil_ph": 5.5,
            "slope": 4.5,
            "land_area": 100.0,
            "lang": "en"
        }
        res = self.client.post('/api/ai/crop-reasoning', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        analysis = data.get("analysis", {})
        self.assertIn(analysis.get("mode"), ["LIVE_GEMINI", "AUTONOMOUS_RULE_ENGINE"])

    def test_14_crop_reasoning_forced_local_advisory_fallback(self):
        """Ensure failed Gemini reasoning returns a non-certifying local preview."""
        payload = {
            "palm_age": 7.5,
            "crops": ["Jahe Merah"],
            "soil_ph": 5.2,
            "slope": 5.0,
            "land_area": 50.0,
            "lang": "en"
        }
        # Simulate Gemini failure by patching generate_crop_agroecological_reasoning to raise exception
        with patch('ai_service.client', None):
            with patch('google.genai.Client', side_effect=Exception("Simulated API Quota Exceeded")):
                from ai_service import generate_crop_agroecological_reasoning
                result = generate_crop_agroecological_reasoning(
                    palm_age=7.5,
                    crops=["Jahe Merah"],
                    soil_ph=5.2,
                    slope=5.0,
                    land_area=50.0,
                    lang='en'
                )
                self.assertEqual(result.get("mode"), "AUTONOMOUS_RULE_ENGINE")
                self.assertTrue(result.get("is_fallback"))
                self.assertIn("[AUDIT NOTICE]", result.get("audit_notice", ""))
                self.assertIn("not a compliance verifier", result.get("engine", ""))
                self.assertEqual(result.get("verdict"), "REQUIRES_FIELD_REVIEW")
                self.assertNotIn("VERIFIED COMPLIANT", result.get("statutory_compliance", ""))
                self.assertIn("canopy_par_evaluation", result)
                self.assertIn("root_buffer_protection", result)

                with patch('app.generate_crop_agroecological_reasoning', return_value=result):
                    with patch('app.record_unified_ai_log') as record_log:
                        response = self.client.post('/api/ai/crop-reasoning', json=payload)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.get_json()["analysis"]["is_fallback"])
                record_log.assert_called_once()
                self.assertEqual(record_log.call_args.kwargs["status"], "FALLBACK")
                self.assertEqual(record_log.call_args.kwargs["engine_mode"], "AUTONOMOUS_STATUTORY_RULE_ENGINE")

        failing_client = Mock()
        failing_client.models.generate_content.side_effect = RuntimeError("Simulated Gemini outage")
        with patch('ai_service.client', failing_client):
            with patch('ai_service.record_ai_log') as record_ai_log:
                from ai_service import generate_crop_agroecological_reasoning
                result = generate_crop_agroecological_reasoning(
                    palm_age=7.5,
                    crops=["Jahe Merah"],
                    soil_ph=5.2,
                    slope=5.0,
                    land_area=50.0,
                    lang='en'
                )
        self.assertTrue(result.get("is_fallback"))
        self.assertEqual(result.get("verdict"), "REQUIRES_FIELD_REVIEW")
        self.assertIn("not a compliance verifier", result.get("engine", ""))
        record_ai_log.assert_called_once()
        self.assertEqual(record_ai_log.call_args.kwargs["engine_mode"], "AUTONOMOUS_STATUTORY_RULE_ENGINE")

    # =========================================================================
    # 5. TEST MULTIMODAL VISION SCANNER API & DUAL-ENGINE FALLBACK
    # =========================================================================
    def test_15_scan_image_standard(self):
        """Test POST /api/ai/scan-image standard payload"""
        payload = {
            "image_url": "/static/img/sawit_drone.jpg",
            "filename": "sawit_drone.jpg",
            "dossier_id": "EST-MDN-010",
            "perspective_mode": "AERIAL_DRONE",
            "declared_crop": "Jahe Merah"
        }
        res = self.client.post('/api/ai/scan-image', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn(data.get("mode"), ["LIVE_GEMINI", "AUTONOMOUS_RULE_ENGINE"])
        self.assertIn("physical_entities", data)

    def test_16_scan_image_forced_autonomous_rule_engine(self):
        """Test POST /api/ai/scan-image forced Mode B fallback when Gemini vision throws"""
        payload = {
            "image_url": "/static/img/sawit_drone.jpg",
            "filename": "sawit_drone.jpg",
            "dossier_id": "EST-MDN-010",
            "perspective_mode": "AERIAL_DRONE"
        }
        with patch('cloud_services.grounded_auditor.audit_image_with_gemini', side_effect=Exception("Simulated Network Timeout")):
            res = self.client.post('/api/ai/scan-image', json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("status"), "success")
            self.assertEqual(data.get("mode"), "AUTONOMOUS_RULE_ENGINE")
            self.assertTrue(data.get("is_fallback"))
            self.assertFalse(data.get("api_telemetry", {}).get("is_live_gemini_called"))
            self.assertIn("[AUDIT NOTICE]", data.get("audit_notice", ""))
            self.assertIn("Simulated Network Timeout", data.get("audit_notice", ""))
            self.assertEqual(
                data.get("api_telemetry", {}).get("error_message"),
                "Simulated Network Timeout",
            )
            self.assertIn("Simulated Network Timeout", data.get("warning", ""))
            self.assertIn("Autonomous Statutory Rule Engine", data.get("engine", ""))
            entities = data.get("physical_entities", [])
            self.assertGreater(len(entities), 0)
            self.assertTrue(all(entity.get("is_heuristic") for entity in entities))
            self.assertTrue(all("confidence" not in entity for entity in entities))

    def test_17_scan_image_marks_non_live_auditor_result_as_fallback(self):
        """A successful function return is not proof that Gemini inference succeeded."""
        fallback_result = {
            "api_telemetry": {
                "is_live_gemini_called": False,
                "api_call_status": "FALLBACK_ENGAGED",
                "error_message": "Gemini unavailable"
            },
            "physical_entities": [],
            "detected_objects": []
        }
        with patch(
            'cloud_services.grounded_auditor.audit_image_with_gemini',
            return_value=fallback_result
        ), patch('app.update_server_with_latest_scan') as persist_scan:
            res = self.client.post('/api/ai/scan-image', json={
                "image_url": "/static/img/sawit_drone.jpg",
                "filename": "sawit_drone.jpg",
                "perspective_mode": "AERIAL_DRONE"
            })

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("mode"), "AUTONOMOUS_RULE_ENGINE")
        self.assertTrue(data.get("is_fallback"))
        self.assertFalse(data.get("api_telemetry", {}).get("is_live_gemini_called"))
        self.assertIn("not image-verified", data.get("audit_notice", ""))
        self.assertIn("Gemini unavailable", data.get("audit_notice", ""))
        persist_scan.assert_not_called()

    def test_spatial_save_reports_database_commit_failure(self):
        connection = Mock()
        connection.execute.side_effect = sqlite3.OperationalError(
            "simulated SQLite write failure"
        )
        response = None

        with patch("app.get_pure_db_connection", return_value=connection):
            response = self.client.post(
                "/api/spatial/save-inspection",
                json={"kode_kebun": "EST-MDN-010", "surveillance_entries": []},
            )

        self.assertEqual(response.status_code, 500)
        result = response.get_json()
        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status"), "error")
        self.assertIn("simulated SQLite write failure", result.get("error", ""))
        connection.rollback.assert_called_once()
        connection.close.assert_called_once()

    def test_18_scan_image_uses_uploaded_image_mime_type(self):
        """PNG uploads must reach Gemini with their actual MIME type."""
        live_result = {
            "api_telemetry": {
                "is_live_gemini_called": True,
                "api_call_status": "LIVE_GOOGLE_CLOUD_SUCCESS",
                "model_invoked": "gemini-test"
            },
            "physical_entities": [
                {"label": "palm_crown", "box_2d": [10, 10, 100, 100]},
                {"label": "alley", "box_2d": [200, 200, 300, 300]}
            ],
            "detected_objects": []
        }
        with patch(
            'cloud_services.grounded_auditor.audit_image_with_gemini',
            return_value=live_result
        ) as audit_image:
            res = self.client.post(
                '/api/ai/scan-image',
                data={"image": (BytesIO(b"not-a-real-png"), "inspection.png")},
                content_type="multipart/form-data"
            )

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("mode"), "LIVE_GEMINI")
        self.assertFalse(data.get("is_fallback"))
        self.assertEqual(audit_image.call_args.kwargs.get("mime_type"), "image/png")

    def test_scan_image_logs_simulator_prompt_context_and_raw_model_response(self):
        prompt_used = "Analyze the image.\nWORKFLOW CONTEXT: simulator calibration."
        raw_model_response = '{"physical_entities":[{"label":"oil palm"}]}'
        live_result = {
            "api_telemetry": {
                "is_live_gemini_called": True,
                "api_call_status": "LIVE_GOOGLE_CLOUD_SUCCESS",
                "model_invoked": "gemini-test"
            },
            "physical_entities": [{"label": "oil palm", "box_2d": [10, 10, 100, 100]}],
            "detected_objects": [],
            "_audit_prompt": prompt_used,
            "_raw_machine_response": raw_model_response
        }
        payload = {
            "image_url": "/static/img/sawit_drone.jpg",
            "filename": "simulator-evidence.jpg",
            "dossier_id": "EST-MDN-010",
            "perspective_mode": "AERIAL_DRONE",
            "page_context": "SIMULATOR",
            "feature_name": "Incorrect generic feature",
            "meta_info": "In-silico calibration",
            "scan_context": {
                "workflow": "In-silico simulator",
                "purpose": "Calibrate visible entity context",
                "filename": "simulator-evidence.jpg"
            }
        }
        with patch(
            "cloud_services.grounded_auditor.audit_image_with_gemini",
            return_value=live_result
        ) as audit_image, patch(
            "cloud_services.agentic_vision_supervisor.FieldVisionSupervisorAgent.evaluate_and_supervise",
            side_effect=lambda raw_analysis, **kwargs: raw_analysis
        ), patch("app.record_unified_ai_log") as record_log:
            response = self.client.post("/api/ai/scan-image", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            audit_image.call_args.kwargs["scan_context"]["workflow"],
            "In-silico simulator"
        )
        self.assertEqual(
            record_log.call_args.kwargs["feature_name"],
            "Simulator In-Silico Vision Scan"
        )
        self.assertEqual(record_log.call_args.kwargs["prompt_input"], prompt_used)
        self.assertEqual(record_log.call_args.kwargs["raw_response"], raw_model_response)

    def test_scan_image_logs_timeline_stage_context(self):
        live_result = {
            "api_telemetry": {
                "is_live_gemini_called": True,
                "api_call_status": "LIVE_GOOGLE_CLOUD_SUCCESS",
                "model_invoked": "gemini-test"
            },
            "physical_entities": [],
            "detected_objects": [],
            "_audit_prompt": "Timeline stage Q2 prompt",
            "_raw_machine_response": '{"physical_entities":[]}'
        }
        payload = {
            "image_url": "/static/img/sawit_drone.jpg",
            "filename": "stage-q2.jpg",
            "dossier_id": "EST-MDN-010",
            "perspective_mode": "TERRESTRIAL_IN_SITU",
            "page_context": "TIMELINES",
            "stage_index": 2,
            "scan_context": {
                "workflow": "Quarterly surveillance timeline",
                "cycle": "Q2",
                "stage_title": "Quarter 2 Intercrop Corridor & Soil Integrity",
                "surveillance_focus": "Intercrop corridor"
            }
        }
        with patch(
            "cloud_services.grounded_auditor.audit_image_with_gemini",
            return_value=live_result
        ) as audit_image, patch(
            "cloud_services.agentic_vision_supervisor.FieldVisionSupervisorAgent.evaluate_and_supervise",
            side_effect=lambda raw_analysis, **kwargs: raw_analysis
        ), patch("app.record_unified_ai_log") as record_log:
            response = self.client.post("/api/ai/scan-image", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            audit_image.call_args.kwargs["scan_context"]["cycle"],
            "Q2"
        )
        self.assertEqual(
            record_log.call_args.kwargs["feature_name"],
            "Timelines Quarterly Surveillance Vision Scan"
        )
        self.assertEqual(
            record_log.call_args.kwargs["prompt_input"],
            "Timeline stage Q2 prompt"
        )
        self.assertEqual(
            record_log.call_args.kwargs["raw_response"],
            '{"physical_entities":[]}'
        )

    def test_ai_log_keeps_full_scan_prompt_and_raw_response(self):
        import ai_service
        from cloud_services.bigquery_logger import _save_ai_log_to_sqlite

        long_prompt = "P" * 2000
        long_response = "R" * 4000
        with patch("ai_service.send_ai_log_to_bigquery_async") as send_log:
            ai_service.record_ai_log(
                "Simulator In-Silico Vision Scan",
                "Google Cloud (gemini-test)",
                1500,
                "SUCCESS",
                long_prompt,
                long_response
            )

        self.assertEqual(send_log.call_args.args[4], long_prompt)
        self.assertEqual(send_log.call_args.args[5], long_response)
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "scan-logs.db")
            with patch("cloud_services.bigquery_logger.DB_PATH", db_path):
                _save_ai_log_to_sqlite(
                    "2026-10-25 22:00:00 WIB",
                    "Simulator In-Silico Vision Scan",
                    "Google Cloud (gemini-test)",
                    1500,
                    "SUCCESS",
                    long_prompt,
                    long_response,
                    "TEST_HASH"
                )
            connection = sqlite3.connect(db_path)
            try:
                stored_prompt, stored_response = connection.execute(
                    "SELECT prompt_input, raw_response FROM ai_execution_logs"
                ).fetchone()
            finally:
                connection.close()
            self.assertEqual(stored_prompt, long_prompt)
            self.assertEqual(stored_response, long_response)

    def test_grounded_vision_prompt_uses_scan_context_as_unverified_metadata(self):
        from cloud_services.grounded_auditor import audit_image_with_gemini

        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            result = audit_image_with_gemini(
                image_bytes=b"test image bytes",
                filename="stage-q2.jpg",
                perspective_mode="TERRESTRIAL_IN_SITU",
                scan_context={
                    "workflow": "Quarterly surveillance timeline",
                    "cycle": "Q2",
                    "surveillance_focus": "Intercrop corridor"
                }
            )

        prompt = result["_audit_prompt"]
        self.assertIn('"cycle": "Q2"', prompt)
        self.assertIn("metadata, not proof of image contents", prompt)
        self.assertIn("do not assume a stage focus", prompt)
        self.assertIn(
            '"reason": "GEMINI_API_KEY is not set in the active environment.',
            result["_raw_machine_response"],
        )

    # =========================================================================
    # 6. TEST FULL-STACK SIMULATION PERSISTENCE (ONE-CLICK AUDIT PERSISTENCE)
    # =========================================================================
    def test_19_api_simulate_persistence(self):
        """Test POST /api/simulate direct persistence"""
        payload = {
            "id_kebun": 10,
            "kode_kebun": "EST-MDN-010",
            "palm_age": 7.0,
            "land_area": 100.0,
            "crop_name": "Red Ginger (Zingiber officinale var. rubrum)",
            "yield_palm_inter": 22.5,
            "yield_palm_mono": 24.0,
            "yield_crop_inter": 7.5,
            "yield_crop_mono": 15.0,
            "slope": 4.5,
            "elevation": 142.0,
            "total_ler": 1.4375,
            "avoided_land_ha": 43.75,
            "carbon_tco2e": 19688,
            "lai": 4.85,
            "biomass_t_ha": 128.4,
            "economic_benefit_usd": 4900.0,
            "ai_reasoning": {
                "analysis_text": "Polyculture compatibility verified compliant under PPKS standards.",
                "sha256_seal": "8F43TESTSEAL1234567890ABCDEF",
                "verdict": "VERIFIED COMPLIANT (S1)"
            }
        }
        res = self.client.post(
            '/api/simulate',
            json=payload,
            headers={'Idempotency-Key': f"sim-test-{uuid.uuid4().hex}"},
        )
        self.assertIn(res.status_code, (200, 201))
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("commit_status"), "COMMITTED")
        self.assertEqual(data.get("ledger", {}).get("authority"), "LOCAL_SQLITE")
        self.assertTrue("id" in data or "record_id" in data)

    # =========================================================================
    # 7. TEST MOBILE FOREMAN VOICE REPORT & FALLBACK
    # =========================================================================
    def test_18_mobile_voice_report(self):
        """Test POST /api/mobile/voice-report fallback parsing"""
        payload = {
            "dossier_id": "EST-MDN-010",
            "transcript": "Piringan sawit bersih 2 meter bebas gulma, tanaman jahe merah tumbuh subur di lorong sela 3.79m."
        }
        res = self.client.post('/api/mobile/voice-report', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")

    # =========================================================================
    # 8. TEST SPATIAL EVIDENCE ANALYSIS & BOUNDARY VERIFICATION
    # =========================================================================
    def test_19_spatial_evidence_analysis(self):
        """Test POST /api/spatial/evidence-analysis"""
        payload = {
            "dossier_id": "EST-MDN-010",
            "lat": 0.824102,
            "lng": 99.561214,
            "polygon": [[99.560, 0.824], [99.562, 0.824], [99.562, 0.826], [99.560, 0.826]]
        }
        res = self.client.post('/api/spatial/evidence-analysis', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")

if __name__ == '__main__':
    unittest.main()
