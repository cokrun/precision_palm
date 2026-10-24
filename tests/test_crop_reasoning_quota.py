import types
import unittest
from unittest.mock import Mock, patch

import ai_service
import app as app_module


class TestCropReasoningQuotaFallback(unittest.TestCase):
    def test_quota_error_returns_advisory_fallback_and_retry_delay(self):
        client = types.SimpleNamespace(
            models=types.SimpleNamespace(
                generate_content=Mock(
                    side_effect=RuntimeError(
                        "429 RESOURCE_EXHAUSTED: quota exceeded; retry in 31s"
                    )
                )
            )
        )
        sdk_types = types.SimpleNamespace(
            GenerateContentConfig=lambda **kwargs: kwargs
        )

        with patch.object(ai_service, "client", client), patch.object(
            ai_service, "types", sdk_types
        ), patch.object(ai_service, "record_ai_log") as record_log:
            result = ai_service.generate_crop_agroecological_reasoning(
                7.5, ["Red Ginger"], lang="en"
            )

        self.assertEqual(result["mode"], "AUTONOMOUS_RULE_ENGINE")
        self.assertTrue(result["is_fallback"])
        self.assertEqual(result["fallback_reason"], "QUOTA_EXHAUSTED")
        self.assertEqual(result["retry_after_seconds"], 31)
        self.assertIn("No automatic retry", result["audit_notice"])
        record_log.assert_called_once()
        self.assertEqual(record_log.call_args.kwargs["status_message"], result["audit_notice"])
        client.models.generate_content.assert_called_once()

    def test_api_preserves_quota_fallback_notice(self):
        fallback = {
            "mode": "AUTONOMOUS_RULE_ENGINE",
            "is_fallback": True,
            "fallback_reason": "QUOTA_EXHAUSTED",
            "retry_after_seconds": 31,
            "audit_notice": "Gemini quota is exhausted. Wait 31 seconds before retrying.",
        }
        with patch.object(
            app_module, "generate_crop_agroecological_reasoning", return_value=fallback
        ), patch.object(app_module, "record_unified_ai_log"):
            response = app_module.app.test_client().post(
                "/api/ai/crop-reasoning",
                json={"palm_age": 7.5, "crops": ["Red Ginger"]},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["analysis"]["fallback_reason"], "QUOTA_EXHAUSTED")
        self.assertEqual(payload["analysis"]["retry_after_seconds"], 31)
        self.assertIn("Wait 31 seconds", payload["analysis"]["audit_notice"])


if __name__ == "__main__":
    unittest.main()
