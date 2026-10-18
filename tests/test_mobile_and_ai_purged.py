"""
tests/test_mobile_and_ai_purged.py
Verification suite for complete eradication of hidden mockups, synthetic seed fallbacks,
and hardcoded coordinates across Mobile PWA and AI scripts.
"""

import os
import unittest
import re
from app import app


class TestMobileAndAiPurged(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.app_client = app.test_client()

    def _read_file(self, rel_path):
        full_path = os.path.join(self.base_dir, rel_path)
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()

    def test_mobile_camera_purged(self):
        """1. mobile_camera.js must not contain mock constants or fallback boxes."""
        content = self._read_file(os.path.join("mobile", "js", "mobile_camera.js"))
        self.assertNotIn("DEFAULT_PALM_DIAGNOSTICS", content)
        self.assertNotIn("REAL_PHYSICAL_ENTITIES", content)
        self.assertNotIn("fallbackPhysicalEntities", content)
        self.assertNotIn("fallbackDiag", content)
        self.assertIn("latestBoundingBoxes = []", content)

    def test_mobile_db_purged(self):
        """2. mobile_db.js must not have dummy fallback array for estates."""
        content = self._read_file(os.path.join("mobile", "js", "mobile_db.js"))
        self.assertNotIn("EST-MDN-001", content)
        self.assertNotIn("EST-MDN-002", content)
        self.assertIn("estates_cache", content)

    def test_mobile_gps_purged(self):
        """3. mobile_gps.js must initialize coords to null and show GPS waiting status."""
        content = self._read_file(os.path.join("mobile", "js", "mobile_gps.js"))
        self.assertIn("lat: null", content)
        self.assertIn("lng: null", content)
        self.assertIn("[Menunggu Kunci Satelit GPS]", content)
        self.assertNotIn("26.6°C Cerah Berawan (BMKG)", content)

    def test_mobile_index_html_purged(self):
        """4. mobile/index.html must not contain static estate options or hardcoded coords."""
        content = self._read_file(os.path.join("mobile", "index.html"))
        self.assertNotIn('<option value="EST-MDN-010">', content)
        self.assertNotIn('0.824100', content)
        self.assertNotIn('99.561200', content)
        self.assertNotIn('dossier_id=EST-MDN-001', content)
        self.assertIn('[Menunggu Kunci Satelit GPS]', content)

    def test_static_ai_triggers_purged(self):
        """5. static scripts must not have hardcoded coordinate or estate fallbacks."""
        triggers_content = self._read_file(os.path.join("static", "js", "global_ai_triggers.js"))
        self.assertNotIn('"0.824100"', triggers_content)
        self.assertNotIn('"99.561200"', triggers_content)

        audit_content = self._read_file(os.path.join("static", "js", "gemini_audit.js"))
        self.assertNotIn('"EST-MDN-001"', audit_content)

    def test_mobile_endpoint_response(self):
        """6. GET /mobile must render an honest empty state with no mock coordinates."""
        response = self.app_client.get('/mobile')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertNotIn('<option value="EST-MDN-010">', html)
        self.assertNotIn('0.824100', html)
        self.assertNotIn('99.561200', html)
        self.assertIn('[Menunggu Kunci Satelit GPS]', html)

    def test_phase2_redundant_files_deleted(self):
        """7. Ensure slide.html, slide_deck.html, and pendaftaran_2.html are deleted."""
        for filename in ["slide.html", "slide_deck.html", "pendaftaran_2.html"]:
            path = os.path.join(self.base_dir, "templates", filename)
            self.assertFalse(os.path.exists(path), f"File {filename} should be deleted!")

    def test_phase2_template_corrections(self):
        """8. Ensure validasi.html dynamic weather binding and teknologi.html model label."""
        validasi_html = self._read_file(os.path.join("templates", "validasi.html"))
        self.assertIn("log.weather_satellite_validation", validasi_html)
        self.assertIn("BMKG Matched", validasi_html)

        teknologi_html = self._read_file(os.path.join("templates", "teknologi.html"))
        self.assertIn("Model: gemini-3.8-flash", teknologi_html)
        self.assertNotIn("Model: gemini-2.5-flash", teknologi_html)


if __name__ == '__main__':
    unittest.main()
