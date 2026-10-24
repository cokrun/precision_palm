import unittest

from ai_service import build_universal_vision_package


class TestUniversalVisionPackage(unittest.TestCase):
    def test_live_package_does_not_invent_measurements_or_validation(self):
        package = build_universal_vision_package({}, telemetry={}, is_live=True)

        self.assertIsNone(package["realistic_image_match_pct"])
        self.assertEqual(package["match_tier"], "GROUND_TRUTH_REQUIRED")
        self.assertEqual(package["spatial_vector"], {
            "status": "MODEL_OUTPUT_NOT_GROUND_TRUTH_VERIFIED"
        })
        self.assertEqual(package["biophysical_vector"], {
            "status": "MODEL_OUTPUT_NOT_GROUND_TRUTH_VERIFIED"
        })
        self.assertIsNone(package["forensic_vector"]["discrepancy_score"])
        self.assertIsNone(package["forensic_vector"]["ppks_root_ring_205cm"]["compliant"])
        self.assertIsNone(package["forensic_vector"]["image_sha256_hash"])

    def test_package_preserves_explicit_model_and_telemetry_values(self):
        package = build_universal_vision_package(
            {
                "canopy_density_pct": 41.2,
                "potential_ler": 1.1,
                "observed_taxon": "Model-reported taxon",
            },
            telemetry={
                "latitude": 0.5,
                "longitude": 100.25,
                "altitude_agl_m": 12,
            },
            is_live=True,
        )

        self.assertEqual(package["spatial_vector"]["coordinates"], {
            "lat": 0.5,
            "lng": 100.25,
        })
        self.assertEqual(package["spatial_vector"]["altitude_agl_m"], 12)
        self.assertEqual(package["biophysical_vector"]["canopy_density_pct"], 41.2)
        self.assertEqual(package["biophysical_vector"]["potential_ler"], 1.1)
        self.assertEqual(package["forensic_vector"]["observed_taxon"], "Model-reported taxon")

    def test_match_score_requires_explicit_validated_ground_truth(self):
        unvalidated = build_universal_vision_package(
            {
                "discrepancy_score": 0.03,
                "ground_truth_validation": {
                    "validated": False,
                    "match_pct": 94.6,
                },
            },
            is_live=True,
        )
        validated = build_universal_vision_package(
            {
                "ground_truth_validation": {
                    "validated": True,
                    "match_pct": 91.0,
                    "discrepancy_score": 0.12,
                },
            },
            is_live=True,
        )

        self.assertIsNone(unvalidated["realistic_image_match_pct"])
        self.assertIsNone(unvalidated["forensic_vector"]["discrepancy_score"])
        self.assertEqual(validated["realistic_image_match_pct"], 91.0)
        self.assertEqual(validated["forensic_vector"]["discrepancy_score"], 0.12)

    def test_fallback_package_is_marked_unverified(self):
        package = build_universal_vision_package(
            {"canopy_density_pct": 52.4},
            is_live=False,
        )

        self.assertEqual(package["match_tier"], "NOT_IMAGE_VERIFIED")
        self.assertEqual(package["biophysical_vector"]["status"], "NOT_IMAGE_VERIFIED")
        self.assertEqual(package["biophysical_vector"]["canopy_density_pct"], 52.4)


if __name__ == "__main__":
    unittest.main()
