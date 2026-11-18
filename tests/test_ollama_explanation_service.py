import json
import os
import unittest
from io import BytesIO
from unittest.mock import Mock, patch
from urllib.error import URLError

from ollama_explanation_service import (
    DEFAULT_OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_REQUEST_TIMEOUT_SECONDS,
    LocalExplanationContext,
    LocalExplanationStatus,
    generate_local_career_explanation,
)


def explanation_context():
    return LocalExplanationContext(
        career_name="Data Analyst",
        matched_skills=("SQL", "Data Analysis"),
        missing_skills=("Statistics", "Python"),
        interests=("Data Science", "Business & Management"),
        recommendation_score=72.5,
    )


class OllamaExplanationServiceTests(unittest.TestCase):
    def test_successful_local_generation_uses_configured_ollama_model_and_endpoint(self):
        opener = Mock(return_value=BytesIO(
            b'{"response":"Your SQL and data analysis matches support this path."}'
        ))

        result = generate_local_career_explanation(
            explanation_context(),
            opener=opener,
        )

        self.assertEqual(result.status, LocalExplanationStatus.SUCCESS)
        self.assertTrue(result.succeeded)
        self.assertEqual(
            result.text,
            "Your SQL and data analysis matches support this path.",
        )
        request = opener.call_args.args[0]
        self.assertEqual(
            request.full_url,
            f"{DEFAULT_OLLAMA_HOST}/api/generate",
        )
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["model"], OLLAMA_MODEL)
        self.assertFalse(body["stream"])
        self.assertEqual(opener.call_args.kwargs["timeout"], OLLAMA_REQUEST_TIMEOUT_SECONDS)

    def test_ollama_host_can_be_configured_without_credentials(self):
        opener = Mock(return_value=BytesIO(b'{"response":"A local explanation."}'))
        with patch.dict(os.environ, {"OLLAMA_HOST": "http://127.0.0.1:11435/"}):
            result = generate_local_career_explanation(
                explanation_context(),
                opener=opener,
            )

        self.assertTrue(result.succeeded)
        self.assertEqual(
            opener.call_args.args[0].full_url,
            "http://127.0.0.1:11435/api/generate",
        )

    def test_unavailable_ollama_returns_rule_based_fallback(self):
        opener = Mock(side_effect=URLError("private connection details"))

        result = generate_local_career_explanation(
            explanation_context(),
            opener=opener,
        )

        self.assertEqual(result.status, LocalExplanationStatus.UNAVAILABLE)
        self.assertIn("Data Analyst", result.fallback_text)
        self.assertIn("SQL, Data Analysis", result.fallback_text)
        self.assertIn("72.5/100", result.fallback_text)
        self.assertIn("not AI-generated", result.fallback_text)
        self.assertEqual(result.diagnostic, "category=unavailable")

    def test_timeout_returns_rule_based_fallback(self):
        opener = Mock(side_effect=TimeoutError("private timeout detail"))

        result = generate_local_career_explanation(
            explanation_context(),
            opener=opener,
        )

        self.assertEqual(result.status, LocalExplanationStatus.TIMEOUT)
        self.assertTrue(result.fallback_text)
        self.assertEqual(result.diagnostic, "category=timeout")

    def test_malformed_response_returns_rule_based_fallback(self):
        opener = Mock(return_value=BytesIO(b'{"response": null}'))

        result = generate_local_career_explanation(
            explanation_context(),
            opener=opener,
        )

        self.assertEqual(result.status, LocalExplanationStatus.INVALID_RESPONSE)
        self.assertTrue(result.fallback_text)
        self.assertEqual(result.diagnostic, "category=invalid_response")

    def test_prompt_contains_only_recommendation_data(self):
        opener = Mock(return_value=BytesIO(b'{"response":"Local explanation."}'))

        result = generate_local_career_explanation(
            explanation_context(),
            opener=opener,
        )

        self.assertTrue(result.succeeded)
        request_payload = json.loads(opener.call_args.args[0].data.decode("utf-8"))
        prompt = request_payload["prompt"]
        data = json.loads(prompt.split("Recommendation data:\n", 1)[1])
        self.assertEqual(
            set(data),
            {
                "career_name",
                "matched_skills",
                "missing_skills",
                "interests",
                "recommendation_score",
            },
        )
        self.assertEqual(data["career_name"], "Data Analyst")
        self.assertEqual(data["matched_skills"], ["SQL", "Data Analysis"])
        self.assertEqual(data["missing_skills"], ["Statistics", "Python"])
        self.assertEqual(data["interests"], ["Data Science", "Business & Management"])
        self.assertEqual(data["recommendation_score"], 72.5)

    def test_failure_logs_do_not_include_secrets_prompt_or_personal_data(self):
        private_prompt_marker = "private personal assessment marker"
        context = LocalExplanationContext(
            career_name="Data Analyst",
            matched_skills=("SQL", private_prompt_marker),
            missing_skills=("Python",),
            interests=("Data Science",),
            recommendation_score=72.5,
        )
        opener = Mock(
            side_effect=URLError(
                "private transport details and test-only-secret-value"
            )
        )

        with self.assertLogs("ollama_explanation_service", level="WARNING") as captured:
            result = generate_local_career_explanation(context, opener=opener)

        output = "\n".join(captured.output)
        self.assertEqual(result.status, LocalExplanationStatus.UNAVAILABLE)
        self.assertIn("category=unavailable", output)
        self.assertNotIn(private_prompt_marker, output)
        self.assertNotIn("private transport details", output)
        self.assertNotIn("test-only-secret-value", output)
        self.assertNotIn("GEMINI_API_KEY", output)

    def test_invalid_endpoint_configuration_falls_back_without_request(self):
        opener = Mock()
        with patch.dict(
            os.environ,
            {"OLLAMA_HOST": "http://user:password@localhost:11434"},
        ):
            result = generate_local_career_explanation(
                explanation_context(),
                opener=opener,
            )

        self.assertEqual(
            result.status,
            LocalExplanationStatus.INVALID_CONFIGURATION,
        )
        self.assertTrue(result.fallback_text)
        opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
