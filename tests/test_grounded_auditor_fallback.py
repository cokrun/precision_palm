import unittest
import os
from unittest.mock import patch

import app as server
from cloud_services.grounded_auditor import GroundedStatutoryAuditor


class TestGroundedAuditorFallback(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()

    def test_local_fallback_uses_only_matched_corpus_sources(self):
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "",
            "GCP_PROJECT_ID": "",
            "VERTEX_AI_ENABLED": "false"
        }):
            auditor = GroundedStatutoryAuditor(gemini_api_key="")
            result = auditor.query_auditor("2.0m sterile root buffer zero-tillage", lang="en")

        self.assertTrue(result["is_fallback"])
        self.assertEqual(result["mode"], "LOCAL_GROUNDED_FALLBACK")
        self.assertTrue(result["citations"])
        self.assertIn("Local fallback", result["answer"])
        self.assertIn(result["citations"][0]["doc_title"], result["answer"])
        self.assertNotIn("4.2 times", result["answer"])

    def test_unmatched_question_does_not_receive_unrelated_citations(self):
        auditor = GroundedStatutoryAuditor(gemini_api_key="")
        with patch.object(auditor, "find_relevant_documents", return_value=[]):
            result = auditor.query_auditor("Explain an unrelated topic.", lang="en")

        self.assertTrue(result["success"])
        self.assertTrue(result["is_fallback"])
        self.assertEqual(result["mode"], "NO_GROUNDED_SOURCES")
        self.assertEqual(result["citations"], [])
        self.assertIn("cannot determine compliance", result["answer"])
        self.assertEqual(
            result["grounding_metadata"]["attribution_status"],
            "NO_MATCHING_REFERENCES"
        )

    def test_grounded_audit_endpoint_preserves_explicit_fallback_metadata(self):
        result = {
            "success": True,
            "is_fallback": True,
            "mode": "LOCAL_GROUNDED_FALLBACK",
            "fallback_reason": "Vertex AI unavailable",
            "answer": "Local corpus summary.",
            "citations": [{"ref": "[1]", "doc_title": "Source"}],
            "grounding_metadata": {
                "engine": "Local statutory corpus",
                "attribution_status": "CORPUS_REFERENCES_ATTACHED"
            }
        }
        with patch.object(server, "grounded_auditor") as auditor, \
                patch.object(server, "record_unified_ai_log"):
            auditor.query_auditor.return_value = result
            response = self.client.post(
                "/api/ai/grounded-audit",
                json={"query": "test question", "estate_code": "EST-TEST-001"}
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["mode"], "LOCAL_GROUNDED_FALLBACK")
        self.assertTrue(payload["is_fallback"])
        self.assertEqual(payload["fallback_reason"], "Vertex AI unavailable")

    def test_review_save_uses_local_store_when_bigquery_helper_is_unavailable(self):
        local_store = {"node_reviews": []}
        with patch.object(server, "save_node_review_to_bigquery", None), \
                patch.object(server, "read_local_store", return_value=local_store), \
                patch.object(server, "save_local_store"), \
                patch.object(server, "record_unified_ai_log"):
            response = self.client.post(
                "/api/ai/save-node-review",
                json={
                    "node_id": "node_1_1",
                    "estate_code": "EST-TEST-001",
                    "verdict_answer": "Grounded fallback summary.",
                    "citations": [{"ref": "[1]", "doc_title": "Source"}],
                    "audit_mode": "LOCAL_GROUNDED_FALLBACK"
                }
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["storage"], "Local JSON Store")
        self.assertEqual(payload["cloud_sync"], "unavailable")
        self.assertEqual(len(local_store["node_reviews"]), 1)
        self.assertEqual(local_store["node_reviews"][0]["audit_mode"], "LOCAL_GROUNDED_FALLBACK")

    def test_review_save_reports_local_sqlite_and_queued_cloud_sync(self):
        with patch.object(
            server,
            "save_node_review_to_bigquery",
            return_value={"success": True, "sha256_hash": "LOCALHASH"}
        ), patch.object(server, "record_unified_ai_log"):
            response = self.client.post(
                "/api/ai/save-node-review",
                json={
                    "node_id": "node_1_1",
                    "estate_code": "EST-TEST-001",
                    "verdict_answer": "Gemini-grounded answer.",
                    "citations": []
                }
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["storage"], "Local SQLite")
        self.assertEqual(payload["cloud_sync"], "queued")
        self.assertEqual(payload["sha256_hash"], "LOCALHASH")


if __name__ == "__main__":
    unittest.main()
