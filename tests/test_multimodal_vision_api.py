import json
import os
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import Mock, patch

from cloud_services import grounded_auditor


class TestMultimodalVisionApi(unittest.TestCase):
    def test_uses_active_environment_key_and_model_for_gemini_vision(self):
        client = Mock()
        client.models.generate_content.return_value.text = json.dumps({
            "physical_entities": [],
            "auditor_summary": "No objects confidently visible.",
        })
        output = StringIO()

        with (
            patch.dict(os.environ, {
                "GEMINI_API_KEY": "active-test-key",
                "GEMINI_MODEL": "gemini-env-test",
            }),
            patch("google.genai.Client", return_value=client) as client_factory,
            redirect_stdout(output),
        ):
            result = grounded_auditor.audit_image_with_gemini(
                image_bytes=b"image bytes",
                filename="field.jpg",
            )

        self.assertGreaterEqual(client_factory.call_count, 1)
        self.assertTrue(all(
            call.kwargs.get("api_key") == "active-test-key"
            for call in client_factory.call_args_list
        ))
        self.assertEqual(
            client.models.generate_content.call_args.kwargs["model"],
            "gemini-env-test",
        )
        self.assertTrue(result["api_telemetry"]["is_live_gemini_called"])
        self.assertEqual(
            result["api_telemetry"]["api_call_status"],
            "LIVE_GOOGLE_CLOUD_SUCCESS",
        )
        self.assertNotIn("active-test-key", output.getvalue())

    def test_reports_and_logs_gemini_exception_details(self):
        client = Mock()
        client.models.generate_content.side_effect = RuntimeError(
            "Simulated Gemini vision permission denied for active-test-key"
        )
        output = StringIO()

        with (
            patch.dict(os.environ, {"GEMINI_API_KEY": "active-test-key"}),
            patch("google.genai.Client", return_value=client) as client_factory,
            self.assertLogs(grounded_auditor.logger, level="ERROR") as captured_logs,
            redirect_stdout(output),
        ):
            result = grounded_auditor.audit_image_with_gemini(
                image_bytes=b"image bytes",
                filename="field.jpg",
            )

        self.assertGreaterEqual(client_factory.call_count, 1)
        self.assertTrue(all(
            call.kwargs.get("api_key") == "active-test-key"
            for call in client_factory.call_args_list
        ))
        self.assertFalse(result["api_telemetry"]["is_live_gemini_called"])
        self.assertEqual(
            result["api_telemetry"]["api_call_status"],
            "FALLBACK_ENGAGED",
        )
        self.assertIn(
            "Simulated Gemini vision permission denied for [REDACTED]",
            result["api_telemetry"]["error_message"],
        )
        self.assertIn(
            "Simulated Gemini vision permission denied for [REDACTED]",
            result["_raw_machine_response"],
        )
        self.assertTrue(any(
            "Simulated Gemini vision permission denied for [REDACTED]" in log
            for log in captured_logs.output
        ))
        self.assertNotIn("active-test-key", "\n".join(captured_logs.output))
        self.assertNotIn("active-test-key", output.getvalue())


if __name__ == "__main__":
    unittest.main()
