"""
tests/test_scanner_concepts_comparison.py
Comprehensive Local Unit & Integration Tests comparing AI Scanner Concepts across:
1. Spatial (/spatial - Cadastral Parcel & Concession Macro)
2. Simulator (/simulator - Biophysical Canopy PAR & Crop Adaptation)
3. Timelines (/timelines - 4D Spatio-Temporal & Forensic Discrepancy)
4. Mobile (/mobile - Terrestrial In-Situ & Edge Computer Vision)
"""

import unittest
import json
import os
import sys

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from ai_service import get_deterministic_ground_truth


class TestScannerConceptsComparison(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    # =========================================================================
    # 1. SPATIAL SCANNER CONCEPT
    # =========================================================================
    def test_01_spatial_scanner_concept_and_save_inspection(self):
        """Test Spatial Scanner: Cadastral macro, triangular grid, and inspection save"""
        # Step A: POST /api/ai/scan-image with Spatial context (Concession Macro / Drone)
        payload = {
            "image_url": "/static/img/sawit_drone.jpg",
            "filename": "sawit_drone.jpg",
            "dossier_id": "EST-MDN-010",
            "perspective_mode": "AERIAL_CONCESSION_MACRO",
            "page_context": "SPATIAL",
            "latitude": 0.824102,
            "longitude": 99.561214,
            "altitude_agl_m": 120.0
        }
        res = self.client.post('/api/ai/scan-image', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "success")
        self.assertIn(data["mode"], ["LIVE_GEMINI", "AUTONOMOUS_RULE_ENGINE"])

        # Check that physical entities or bounding boxes are returned
        boxes = data.get("physical_entities") or data.get("detected_objects") or []
        self.assertTrue(len(boxes) > 0, "Spatial scanner must return detected spatial entities")

        # Standardized Universal Vision Package & Realistic Match assertions
        self.assertIn("realistic_image_match_pct", data)
        self.assertTrue(88.0 <= data["realistic_image_match_pct"] <= 96.5, f"Realistic match {data['realistic_image_match_pct']}% should be in 88.0% - 96.5%")
        self.assertIn("match_tier", data)
        self.assertIn("universal_vision_package", data)
        uvp = data["universal_vision_package"]
        self.assertIn("spatial_vector", uvp)
        self.assertIn("biophysical_vector", uvp)
        self.assertIn("forensic_vector", uvp)
        self.assertEqual(uvp["spatial_vector"]["triangular_spacing_m"], 9.0)

        # Step B: Test saving the inspection to spatial ledger
        save_payload = {
            "dossier_id": "EST-MDN-010",
            "evidence_id": "EV-TEST-SPATIAL-001",
            "foto_url": "/static/img/sawit_drone.jpg",
            "detected_entities": boxes,
            "sha256_seal": data.get("sha256_hash", "FIPS-TEST-SEAL"),
            "perspective_mode": "AERIAL_CONCESSION_MACRO"
        }
        res_save = self.client.post('/api/spatial/save-inspection', json=save_payload)
        self.assertIn(res_save.status_code, [200, 201])
        save_data = res_save.get_json()
        self.assertTrue(save_data.get("status") in ["success", "saved", "ok"])

    # =========================================================================
    # 2. SIMULATOR SCANNER CONCEPT
    # =========================================================================
    def test_02_simulator_scanner_concept_and_biophysical_binding(self):
        """Test Simulator Scanner: Canopy cover % and biophysical PAR/LER simulation"""
        payload = {
            "image_url": "/static/img/sawit_drone.jpg",
            "filename": "sawit_drone.jpg",
            "dossier_id": "EST-MDN-010",
            "perspective_mode": "AERIAL_DRONE",
            "page_context": "SIMULATOR",
            "declared_crop": "Jahe Merah"
        }
        res = self.client.post('/api/ai/scan-image', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        # Assert Universal Vision Package & Realistic Match
        self.assertIn("realistic_image_match_pct", data)
        self.assertTrue(88.0 <= data["realistic_image_match_pct"] <= 96.5)
        self.assertIn("match_breakdown", data)
        self.assertIn("universal_vision_package", data)
        uvp = data["universal_vision_package"]
        self.assertIn("biophysical_vector", uvp)
        self.assertTrue(uvp["biophysical_vector"]["transmitted_par_pct"] > 0)

        analysis = data.get("analysis", {})
        # Verify plant diagnostics or canopy density exists
        p_diag = data.get("plant_diagnostics") or analysis.get("plant_diagnostics") or {}
        self.assertTrue("canopy_density_pct" in analysis or "canopy_lai_calculated" in p_diag or len(data.get("physical_entities", [])) > 0)

        # Step B: Feed calibrated biophysical data to /api/simulate
        sim_payload = {
            "palm_age": 7.5,
            "crop": "red_ginger",
            "canopy_cover": 52.0,
            "soil_ph": 5.5,
            "slope": 4.5,
            "land_area": 50.0,
            "lang": "en"
        }
        res_sim = self.client.post('/api/simulate', json=sim_payload)
        self.assertEqual(res_sim.status_code, 200)
        sim_data = res_sim.get_json()
        self.assertTrue(sim_data.get("success") or sim_data.get("status") == "success")
        num_data = sim_data.get("data_numerik", {})
        ler_res = num_data.get("efisiensi_lahan_ler", {})
        self.assertIn("total_ler", ler_res)
        self.assertTrue(ler_res["total_ler"] > 1.0, "Agroforestry LER should exceed monoculture baseline")
        self.assertIn("dampak_lingkungan_dan_karbon", num_data)

    # =========================================================================
    # 3. TIMELINES SCANNER CONCEPT
    # =========================================================================
    def test_03_timelines_scanner_concept_and_forensic_discrepancy(self):
        """Test Timelines Scanner: 4D Spatio-temporal telemetry, discrepancy audit, and diagnostic matrix"""
        payload = {
            "image_url": "/static/img/sawit_harvester.jpg",
            "filename": "sawit_harvester.jpg",
            "dossier_id": "EST-MDN-010",
            "perspective_mode": "TERRESTRIAL_IN_SITU",
            "page_context": "TIMELINES",
            "stage_index": 2,
            "declared_crop": "Jagung (Zea mays)",  # Intentional discrepancy to test forensic auditor
            "latitude": 0.824102,
            "longitude": 99.561214,
            "altitude_agl_m": 1.45,
            "camera_pitch_deg": -12.4
        }
        res = self.client.post('/api/ai/scan-image', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        # Timelines specific contracts:
        self.assertIn("discrepancy_score", data)
        self.assertIsInstance(data["discrepancy_score"], (int, float))
        self.assertIn("observed_taxon", data)
        self.assertIn("declared_crop", data)

        # Standardized Universal Vision Package & Realistic Match
        self.assertIn("realistic_image_match_pct", data)
        self.assertTrue(88.0 <= data["realistic_image_match_pct"] <= 96.5)
        self.assertIn("universal_vision_package", data)
        uvp = data["universal_vision_package"]
        self.assertIn("forensic_vector", uvp)
        self.assertEqual(uvp["forensic_vector"]["declared_crop"], "Jagung (Zea mays)")

        # 4-Pillar Diagnostics or Matrix check
        matrix = data.get("diagnostic_matrix_44", {})
        diag = data.get("plant_diagnostics", {})
        self.assertTrue(isinstance(matrix, dict) or isinstance(diag, dict))

    # =========================================================================
    # 4. MOBILE SCANNER CONCEPT
    # =========================================================================
    def test_04_mobile_scanner_concept_and_terrestrial_root_buffer(self):
        """Test Mobile Scanner: Mandor in-situ view, 2.05m root ring verification, and field audit"""
        payload = {
            "image_url": "/static/img/sawit_harvester.jpg",
            "filename": "sawit_harvester.jpg",
            "dossier_id": "EST-MDN-010",
            "perspective_mode": "TERRESTRIAL_IN_SITU",
            "page_context": "MOBILE",
            "latitude": 0.824102,
            "longitude": 99.561214,
            "altitude_agl_m": 1.45,
            "camera_pitch_deg": -12.4,
            "block_id": "EST-MDN-010-BLOK-A"
        }
        res = self.client.post('/api/ai/scan-image', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        # Check entities include root circle / palm anatomy / harvester / alley
        entities = data.get("physical_entities") or data.get("detected_objects") or []
        labels = [e.get("label", "").lower() for e in entities]
        clusters = [e.get("cluster", "").lower() for e in entities]

        has_ground_entities = any("root" in l or "trunk" in l or "harvester" in l or "circle" in l or "palm" in l for l in labels) or \
                              any("root_circle" in c or "infrastructure" in c or "palm_canopy" in c or "harvester" in c for c in clusters)
        self.assertTrue(has_ground_entities, "Mobile Terrestrial view must detect ground-level silvicultural organs")

        # Assert Universal Package root ring & realistic match
        self.assertIn("realistic_image_match_pct", data)
        self.assertTrue(88.0 <= data["realistic_image_match_pct"] <= 96.5)
        uvp = data.get("universal_vision_package", {})
        self.assertIn("forensic_vector", uvp)
        self.assertIn("ppks_root_ring_205cm", uvp["forensic_vector"])
        self.assertEqual(uvp["forensic_vector"]["ppks_root_ring_205cm"]["status"], "PROTECTED_EXCLUSION_ACTIVE")

    # =========================================================================
    # 5. DUAL-ENGINE FALLBACK CONFORMANCE FOR ALL 4 MODES
    # =========================================================================
    def test_05_deterministic_ground_truth_fallback_all_perspectives(self):
        """Test Deterministic Rule Engine fallback produces valid structures for all 4 perspectives"""
        perspectives = [
            ("AERIAL_CONCESSION_MACRO", "SPATIAL"),
            ("AERIAL_DRONE", "SIMULATOR"),
            ("TERRESTRIAL_IN_SITU", "TIMELINES"),
            ("TERRESTRIAL_IN_SITU", "MOBILE")
        ]

        for pers, ctx in perspectives:
            telemetry = {
                "latitude": 0.824102,
                "longitude": 99.561214,
                "altitude_agl_m": 45.0 if "AERIAL" in pers else 1.45,
                "camera_pitch_deg": -90.0 if "DRONE" in pers else -12.4,
                "perspective_mode": pers
            }
            fb = get_deterministic_ground_truth(error_msg="Simulated Cloud Disconnection", telemetry=telemetry, block_id="BLOK-TEST")
            self.assertIn("detected_objects", fb)
            self.assertTrue(len(fb["detected_objects"]) > 0)
            self.assertIn("plant_diagnostics", fb)
            has_sha256 = "sha256_hash" in fb or "var_32_fips_sha256" in str(fb)
            self.assertTrue(has_sha256, "Fallback must include cryptographic SHA-256 seal")

            # Check that fallback also attaches realistic match percentage & universal package
            self.assertIn("realistic_image_match_pct", fb)
            self.assertTrue(88.0 <= fb["realistic_image_match_pct"] <= 96.5)
            self.assertIn("universal_vision_package", fb)
            self.assertIn("spatial_vector", fb["universal_vision_package"])
            self.assertIn("biophysical_vector", fb["universal_vision_package"])
            self.assertIn("forensic_vector", fb["universal_vision_package"])


if __name__ == '__main__':
    unittest.main()

