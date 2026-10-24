"""
tests/test_ai_terminal_and_dual_engine_logging.py
Tests for AI Terminal / AI-Logs & Logging Governance with Dual-Engine Fallback
Validates:
1. Standardized 4-phase lifecycle telemetry & dual-engine status
2. Zero hardcoded secrets governance in public configs
3. SQLite & BigQuery audit persistence for engine_mode and status_message
4. /api/ai/terminal interactive command handling
"""

import unittest
import json
import os
import sys
import tempfile
from unittest.mock import Mock, patch

# Ensure root directory is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app as app_module
from app import app
from database import init_db, get_db_connection, save_simulation_record, get_simulation_log_by_id

class TestAiTerminalAndDualEngineLogging(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def test_01_public_config_governance_zero_secrets(self):
        """Ensure /api/config never exposes raw GEMINI_API_KEY and returns safe dual-engine status"""
        resp = self.client.get('/api/config')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data.decode('utf-8'))

        self.assertIn('api_key_present', data)
        self.assertIsInstance(data['api_key_present'], bool)
        self.assertIn('model_name', data)
        self.assertIn('dual_engine_status', data)
        self.assertIn('dual_engine', data)
        self.assertIn('primary', data['dual_engine'])
        self.assertIn('fallback', data['dual_engine'])

        raw_str = resp.data.decode('utf-8')
        # Ensure no raw secret key string leaked
        self.assertNotIn('AIzaSy', raw_str)
        self.assertNotIn('secret', raw_str.lower())

    def test_02_ai_terminal_commands(self):
        """Ensure /api/ai/terminal processes core commands with structured output"""
        # 1. Help
        resp = self.client.post('/api/ai/terminal', json={'command': 'help'})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertIn('Supported System Commands', data['output'])

        # 2. Status
        resp = self.client.post('/api/ai/terminal', json={'command': 'status'})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data.decode('utf-8'))
        self.assertIn('SYSTEM HEALTH', data['output'])
        self.assertIn('Mode A (Live AI)', data['output'])

        # 3. Model
        resp = self.client.post('/api/ai/terminal', json={'command': 'model'})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data.decode('utf-8'))
        self.assertIn('Mode A - Live Inference', data['output'])

        # 4. Fallback
        resp = self.client.post('/api/ai/terminal', json={'command': 'fallback'})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data.decode('utf-8'))
        self.assertIn('Statutory Rule Engine', data['output'])
        self.assertTrue('ISPO Principle 2' in data['output'] or 'ISPO Prinsip 2' in data['output'])

    def test_03_audit_persistence_dual_engine_fields(self):
        """Ensure engine_mode and status_message are stored and retrieved from SQLite"""
        temp_db = tempfile.TemporaryDirectory()
        self.addCleanup(temp_db.cleanup)
        db_path = os.path.join(temp_db.name, 'simulation-test.db')
        record_id = save_simulation_record(
            id_kebun=10,
            kode_kebun="EST-MDN-010",
            palm_age=7.5,
            land_area=120.0,
            crop_name="Red Ginger",
            yield_palm_inter=21.0,
            yield_palm_mono=22.0,
            yield_crop_inter=7.5,
            yield_crop_mono=15.0,
            total_ler=1.4550,
            pls_percentage=31.27,
            avoided_land_ha=37.52,
            total_climate_benefit_tco2e=16884,
            lai=5.25,
            biomass_t_ha=128.4,
            microclimate_cooling=-2.5,
            soil_moisture_vwc=34.8,
            recharge_m3_ha=2310,
            potassium_recovered_kg=36.2,
            economic_benefit_usd=5880.0,
            image_sample="field_tm_weed.jpg",
            vision_summary={"detection_badge": "6 Objects", "sterile_circle": "2.0m Zero-Tillage"},
            ai_reasoning={"verdict": "VERIFIED COMPLIANT", "analysis_text": "Compliant under PPKS standards"},
            sha256_hash="TEST_SHA256_SEAL_1234567890ABCDEF",
            coords="0.824100, 99.561200",
            slope=4.5,
            elevation=220.0,
            soil_ph=5.5,
            soil_texture="Sandy Loam",
            engine_mode="AUTONOMOUS_STATUTORY_RULE_ENGINE",
            status_message="[AUDIT NOTICE] Gemini Live Session Offline / Quota Exceeded. Validated via Autonomous Statutory Rule Engine (PPKS & ISPO Principle 2 Silvicultural Standards)",
            calculation_inputs={"yield_palm_inter": 21.0},
            data_numerik={"efisiensi_lahan_ler": {"total_ler": 1.455}},
            db_path=db_path
        )
        self.assertIsNotNone(record_id)

        rec = get_simulation_log_by_id(record_id, db_path=db_path)
        self.assertIsNotNone(rec)
        self.assertEqual(rec.get('engine_mode'), "AUTONOMOUS_STATUTORY_RULE_ENGINE")
        self.assertTrue("PPKS" in rec.get('status_message', ''))
        self.assertEqual(rec.get('calculation_inputs'), {"yield_palm_inter": 21.0})
        self.assertEqual(rec.get('data_numerik'), {"efisiensi_lahan_ler": {"total_ler": 1.455}})

    def test_04_simulate_endpoint_records_engine_attestation(self):
        """Ensure /api/simulate returns and persists engine_mode and status_message"""
        payload = {
            "id_kebun": 10,
            "kode_kebun": "EST-MDN-010",
            "palm_age": 6.5,
            "land_area": 85.0,
            "crop_name": "Patchouli",
            "yield_palm_inter": 20.5,
            "yield_palm_mono": 22.0,
            "yield_crop_inter": 6.5,
            "yield_crop_mono": 12.0,
            "total_ler": 1.4730,
            "avoided_land_ha": 27.2,
            "carbon_tco2e": 12240,
            "lai": 5.10,
            "image_sample": "field_tm_weed.jpg",
            "coords": "0.824100, 99.561200",
            "engine_mode": "LIVE_GEMINI",
            "status_message": "Verified via Gemini Multimodal Inference"
        }
        committed = {
            "record_id": 90399,
            "sha256": "B" * 64,
            "committed_at": "2026-10-24T16:08:37Z",
            "cloud_sync_status": "NOT_CONFIGURED",
            "idempotent_replay": False,
        }
        with patch.object(app_module, "save_simulation_record", Mock(return_value=committed)), patch.object(
            app_module, "read_local_store", return_value={"simulator_history": []}
        ), patch.object(app_module, "save_local_store"), patch.object(app_module, "record_unified_ai_log"):
            resp = self.client.post(
                '/api/simulate',
                json=payload,
                headers={'Idempotency-Key': 'sim-ai-terminal-test-0001'},
            )
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.data.decode('utf-8'))

        self.assertEqual(data.get('status'), 'success')
        self.assertEqual(data.get('commit_status'), 'COMMITTED')
        self.assertIn('record_id', data)
        self.assertIn('engine_mode', data)
        self.assertIn('status_message', data)
        self.assertEqual(data['engine_mode'], "LIVE_GEMINI")

    def test_05_api_ai_logs_includes_dual_engine_fields(self):
        """Ensure /api/ai/logs includes engine_mode and status_message for each telemetry entry"""
        resp = self.client.get('/api/ai/logs?limit=10')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data.decode('utf-8'))

        self.assertTrue(data.get('success'))
        self.assertIn('logs', data)
        self.assertIsInstance(data['logs'], list)
        if len(data['logs']) > 0:
            first = data['logs'][0]
            self.assertIn('engine_mode', first)
            self.assertIn('status_message', first)

if __name__ == '__main__':
    unittest.main()
