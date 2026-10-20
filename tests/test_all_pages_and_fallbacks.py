#!/usr/bin/env python3
"""
Comprehensive Test Suite for Precision Palm Cloud
Tests all Pages, AI APIs, Governance Config, and Autonomous Statutory Fallbacks.
"""

import os
import sys
import json
import unittest
from io import BytesIO
from unittest.mock import patch

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
        self.assertIn(b"btn_quick_passport_access", res.data)

    def test_06_page_timelines(self):
        """Test GET /timelines (Stage 3: Surveillance Tracking)"""
        res = self.client.get('/timelines', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

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
        """Test GET /api/pricing/tbs-calculation"""
        res = self.client.get('/api/pricing/tbs-calculation?palm_yield_ton_ha=24.0&intercrop_yield_ton_ha=7.5&intercrop_price_idr_kg=18500.0')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("data", data)
        self.assertGreater(data["data"].get("harga_tbs_idr_kg", 0), 0)

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

    def test_14_crop_reasoning_forced_autonomous_rule_engine(self):
        """Test POST /api/ai/crop-reasoning forced Mode B (Autonomous Statutory Rule Engine)"""
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
                self.assertIn("[AUDIT NOTICE]", result.get("audit_notice", ""))
                self.assertIn("Baku Silvikultur PPKS", result.get("engine", ""))
                self.assertIn("canopy_par_evaluation", result)
                self.assertIn("root_buffer_protection", result)

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
            self.assertIn("[AUDIT NOTICE]", data.get("audit_notice", ""))
            self.assertIn("Autonomous Statutory Rule Engine", data.get("engine", ""))
            entities = data.get("physical_entities", [])
            self.assertGreater(len(entities), 0)

    # =========================================================================
    # 6. TEST FULL-STACK SIMULATION PERSISTENCE (ONE-CLICK AUDIT PERSISTENCE)
    # =========================================================================
    def test_17_api_simulate_persistence(self):
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
        res = self.client.post('/api/simulate', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
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
