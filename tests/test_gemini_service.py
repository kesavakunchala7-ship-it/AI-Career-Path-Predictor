import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from google.genai.errors import ClientError
from streamlit.testing.v1 import AppTest

from career_data import CAREERS
from gemini_service import (
    CareerExplanationContext,
    GEMINI_MAX_OUTPUT_TOKENS,
    GEMINI_REQUEST_TIMEOUT_MS,
    GEMINI_THINKING_LEVEL,
    GeminiStatus,
    _build_prompt,
    generate_career_explanation,
)
from ollama_explanation_service import (
    LocalExplanationContext,
    LocalExplanationResult,
    LocalExplanationStatus,
)
from recommendation_engine import has_meaningful_career_match, rank_careers


APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app.py")


def explanation_context():
    return CareerExplanationContext(
        career_title="Data Scientist",
        career_description="Analyze data to find insights.",
        career_skills=("Python", "SQL", "Statistics"),
        career_interests=("Data Science", "Artificial Intelligence"),
        roadmap=("Review Python and statistics.",),
        confirmed_skills=("Python",),
        confirmed_interests=("Data Science",),
        matched_skills=("Python",),
        matched_interests=("Data Science",),
        missing_skills=("SQL", "Statistics"),
        suggested_skills=("SQL", "Statistics", "Data Visualization"),
    )


class GeminiServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path_patch = patch(
            "user_data_store.DATABASE_PATH",
            Path(self.temporary_directory.name) / "user-data.sqlite3",
        )
        self.database_path_patch.start()
        self.addCleanup(self.database_path_patch.stop)
        self.api_key_environment = patch.dict(os.environ, {"GEMINI_API_KEY": "test-only-key"})
        self.api_key_environment.start()
        self.addCleanup(self.api_key_environment.stop)
        self.model_environment = patch.dict(os.environ, {"GEMINI_MODEL": ""})
        self.model_environment.start()
        self.addCleanup(self.model_environment.stop)
        self.authenticated_user_patch = patch(
            "auth_utils.is_authenticated_user",
            return_value=True,
        )
        self.authenticated_name_patch = patch(
            "auth_utils.authenticated_user_name",
            return_value="Test Student",
        )
        self.authenticated_identity_patch = patch(
            "auth_utils.authenticated_user_identity",
            return_value=("https://accounts.google.com", "gemini-test-subject"),
        )
        self.authenticated_user_patch.start()
        self.authenticated_name_patch.start()
        self.authenticated_identity_patch.start()
        self.addCleanup(self.authenticated_user_patch.stop)
        self.addCleanup(self.authenticated_name_patch.stop)
        self.addCleanup(self.authenticated_identity_patch.stop)

    def test_missing_api_configuration_is_reported_without_creating_a_client(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}), patch(
            "gemini_service._read_streamlit_api_key",
            return_value=None,
        ), patch("gemini_service._create_client") as create_client:
            result = generate_career_explanation(explanation_context())

        self.assertEqual(result.status, GeminiStatus.MISSING_CONFIG)
        self.assertIn("GEMINI_API_KEY", result.message)
        self.assertIn("local summary", result.fallback_text)
        self.assertIn("not an AI-generated explanation", result.fallback_text)
        create_client.assert_not_called()

    def test_streamlit_secret_can_supply_the_api_key(self):
        client = Mock()
        client.models.generate_content.return_value = SimpleNamespace(text="Advice.")
        factory = Mock(return_value=client)

        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}), patch(
            "gemini_service._read_streamlit_api_key",
            return_value="streamlit-test-key",
        ):
            result = generate_career_explanation(
                explanation_context(),
                client_factory=factory,
            )

        self.assertTrue(result.succeeded)
        factory.assert_called_once_with("streamlit-test-key")

    def test_successful_response_uses_configured_model_and_returns_text(self):
        client = Mock()
        client.models.generate_content.return_value = SimpleNamespace(
            text="Your Python background connects to this catalog role."
        )
        factory = Mock(return_value=client)

        with patch.dict(os.environ, {"GEMINI_MODEL": "test-model"}):
            result = generate_career_explanation(
                explanation_context(),
                client_factory=factory,
            )

        self.assertEqual(result.status, GeminiStatus.SUCCESS)
        self.assertTrue(result.succeeded)
        self.assertEqual(
            result.text,
            "Your Python background connects to this catalog role.",
        )
        factory.assert_called_once_with("test-only-key")
        self.assertEqual(client.models.generate_content.call_args.kwargs["model"], "test-model")
        self.assertEqual(
            set(client.models.generate_content.call_args.kwargs),
            {"model", "contents", "config"},
        )
        self.assertEqual(
            client.models.generate_content.call_args.kwargs["config"],
            {
                "http_options": {"timeout": GEMINI_REQUEST_TIMEOUT_MS},
                "max_output_tokens": GEMINI_MAX_OUTPUT_TOKENS,
                "thinking_config": {
                    "thinking_level": GEMINI_THINKING_LEVEL,
                },
            },
        )
        client.models.generate_content.assert_called_once()
        prompt = client.models.generate_content.call_args.kwargs["contents"]
        self.assertIn("Do not invent salary", prompt)
        self.assertIn("Required skills not confirmed", prompt)

    def test_successful_request_logs_timing_model_and_available_response_id_safely(self):
        client = Mock()
        client.models.generate_content.return_value = SimpleNamespace(
            text="Advice.",
            response_id="response-abc123",
        )

        with self.assertLogs("gemini_service", level="INFO") as captured:
            result = generate_career_explanation(
                explanation_context(),
                client_factory=Mock(return_value=client),
            )

        output = "\n".join(captured.output)
        self.assertTrue(result.succeeded)
        self.assertRegex(output, r"started_at=\d{4}-\d{2}-\d{2}T[^;]+\+00:00")
        self.assertRegex(output, r"completed_at=\d{4}-\d{2}-\d{2}T[^;]+\+00:00")
        self.assertRegex(output, r"duration_ms=\d+")
        self.assertIn("attempt=1", output)
        self.assertIn("model=gemini-3.8-flash", output)
        self.assertIn("outcome=success", output)
        self.assertIn("http_status=unavailable", output)
        self.assertIn("category=success", output)
        self.assertIn("provider_response_id=response-abc123", output)
        self.assertNotIn("test-only-key", output)
        self.assertNotIn("Analyze data to find insights.", output)
        self.assertNotIn("Student", output)

    def test_failed_retry_logs_each_attempt_with_safe_status_and_request_id(self):
        first_error = type(
            "ServerError",
            (Exception,),
            {
                "code": 503,
                "status": "UNAVAILABLE",
                "response": SimpleNamespace(
                    headers={"X-Goog-Request-Id": "request-503-safe"}
                ),
            },
        )("private response containing test-only-key")
        second_error = type(
            "ServerError",
            (Exception,),
            {
                "code": 504,
                "status": "DEADLINE_EXCEEDED",
                "response": SimpleNamespace(
                    headers={"x-request-id": "request-504-safe"}
                ),
            },
        )("private response containing test-only-key")
        client = Mock()
        client.models.generate_content.side_effect = [first_error, second_error]

        with patch("gemini_service.time.sleep"), self.assertLogs(
            "gemini_service",
            level="INFO",
        ) as captured:
            result = generate_career_explanation(
                explanation_context(),
                client_factory=Mock(return_value=client),
            )

        output = "\n".join(captured.output)
        completion_lines = [
            line for line in captured.output
            if "Gemini request attempt completed:" in line
        ]
        self.assertEqual(result.status, GeminiStatus.TIMEOUT)
        self.assertEqual(len(completion_lines), 2)
        self.assertIn("attempt=1", completion_lines[0])
        self.assertIn("http_status=503", completion_lines[0])
        self.assertIn("category=service_error", completion_lines[0])
        self.assertIn("provider_request_id=request-503-safe", completion_lines[0])
        self.assertIn("retrying=true", completion_lines[0])
        self.assertIn("attempt=2", completion_lines[1])
        self.assertIn("http_status=504", completion_lines[1])
        self.assertIn("category=timeout", completion_lines[1])
        self.assertIn("provider_request_id=request-504-safe", completion_lines[1])
        self.assertNotIn("test-only-key", output)
        self.assertNotIn("private response", output)
        self.assertNotIn("Analyze data to find insights.", output)
        self.assertNotIn("Student", output)
        self.assertEqual(client.models.generate_content.call_count, 2)

    def test_prompt_formats_empty_assessment_and_catalog_fields(self):
        context = CareerExplanationContext(
            career_title="Synthetic Career",
            career_description="Synthetic description.",
            career_skills=(),
            career_interests=(),
            roadmap=(),
            confirmed_skills=(),
            confirmed_interests=(),
            matched_skills=(),
            matched_interests=(),
            missing_skills=(),
            suggested_skills=(),
        )

        prompt = _build_prompt(context)

        self.assertIn("Career from the project catalog: Synthetic Career", prompt)
        self.assertIn("Catalog description: Synthetic description.", prompt)
        self.assertEqual(prompt.count("- None provided"), 9)

    def test_empty_response_is_reported(self):
        client = Mock()
        client.models.generate_content.return_value = SimpleNamespace(text="  ")

        result = generate_career_explanation(
            explanation_context(),
            client_factory=Mock(return_value=client),
        )

        self.assertEqual(result.status, GeminiStatus.EMPTY_RESPONSE)
        self.assertEqual(result.text, "")

    def test_unauthorized_api_failure_is_reported_without_exposing_details(self):
        api_error = type(
            "APIError",
            (Exception,),
            {"code": 401, "status": "UNAUTHENTICATED"},
        )(
            "sensitive provider detail"
        )
        factory = Mock(side_effect=api_error)

        result = generate_career_explanation(
            explanation_context(),
            client_factory=factory,
        )

        self.assertEqual(result.status, GeminiStatus.INVALID_API_KEY)
        self.assertNotIn("sensitive", result.message)
        self.assertEqual(
            result.diagnostic,
            "Phase: client initialization; APIError; Google API HTTP 401 (UNAUTHENTICATED)",
        )

    def test_permission_and_model_errors_are_distinguished(self):
        cases = (
            (403, "PERMISSION_DENIED", GeminiStatus.PERMISSION_ERROR),
            (404, "NOT_FOUND", GeminiStatus.MODEL_UNAVAILABLE),
        )
        for code, api_status, expected_status in cases:
            with self.subTest(code=code):
                api_error = type(
                    "APIError",
                    (Exception,),
                    {"code": code, "status": api_status},
                )("sensitive provider response")
                result = generate_career_explanation(
                    explanation_context(),
                    client_factory=Mock(side_effect=api_error),
                )

                self.assertEqual(result.status, expected_status)
                self.assertEqual(
                    result.diagnostic,
                    f"Phase: client initialization; APIError; "
                    f"Google API HTTP {code} ({api_status})",
                )
                self.assertNotIn("sensitive", result.diagnostic)

    def test_request_bad_request_includes_only_safe_http_metadata(self):
        api_key = "test-only-key"
        raw_message = f"raw provider message containing {api_key}"
        api_error = type(
            "BadRequestError",
            (Exception,),
            {
                "code": 400,
                "status": "INVALID_ARGUMENT",
                "message": raw_message,
                "details": {"message": raw_message},
            },
        )(raw_message)
        client = Mock()
        client.models.generate_content.side_effect = api_error

        with self.assertLogs("gemini_service", level="WARNING") as captured:
            result = generate_career_explanation(
                explanation_context(),
                client_factory=Mock(return_value=client),
            )

        self.assertEqual(result.status, GeminiStatus.BAD_REQUEST)
        self.assertIn("did not accept the explanation request", result.message)
        self.assertNotIn("temporarily unavailable", result.message)
        self.assertEqual(
            result.diagnostic,
            "Phase: request execution; BadRequestError; "
            "model=gemini-3.8-flash; Google API HTTP 400 (INVALID_ARGUMENT)",
        )
        for surfaced_text in (result.message, result.diagnostic, "\n".join(captured.output)):
            self.assertNotIn(raw_message, surfaced_text)
            self.assertNotIn(api_key, surfaced_text)

    def test_request_bad_request_reads_sdk_status_code_and_safe_body_status(self):
        api_key = "test-only-key"
        raw_message = f"private provider message containing {api_key}"
        api_error = type(
            "BadRequestError",
            (Exception,),
            {
                "status_code": 400,
                "body": {
                    "error": {
                        "code": 400,
                        "status": "INVALID_ARGUMENT",
                        "message": raw_message,
                    }
                },
            },
        )(raw_message)
        client = Mock()
        client.models.generate_content.side_effect = api_error

        with self.assertLogs("gemini_service", level="WARNING") as captured:
            result = generate_career_explanation(
                explanation_context(),
                client_factory=Mock(return_value=client),
            )

        self.assertEqual(
            result.diagnostic,
            "Phase: request execution; BadRequestError; "
            "model=gemini-3.8-flash; Google API HTTP 400 (INVALID_ARGUMENT)",
        )
        for surfaced_text in (result.message, result.diagnostic, "\n".join(captured.output)):
            self.assertNotIn(raw_message, surfaced_text)
            self.assertNotIn(api_key, surfaced_text)

    def test_sdk_client_error_exposes_only_safe_structured_status(self):
        private_message = "synthetic private provider message"
        api_error = ClientError(
            400,
            {"error": {"status": "INVALID_ARGUMENT", "message": private_message}},
        )
        client = Mock()
        client.models.generate_content.side_effect = api_error

        with self.assertLogs("gemini_service", level="WARNING") as captured:
            result = generate_career_explanation(
                explanation_context(),
                client_factory=Mock(return_value=client),
            )

        self.assertEqual(result.status, GeminiStatus.BAD_REQUEST)
        self.assertEqual(
            result.diagnostic,
            "Phase: request execution; ClientError; "
            "model=gemini-3.8-flash; Google API HTTP 400 (INVALID_ARGUMENT)",
        )
        self.assertNotIn(private_message, result.message)
        self.assertNotIn(private_message, result.diagnostic)
        self.assertNotIn(private_message, "\n".join(captured.output))

    def test_sdk_bad_request_without_provider_status_reports_safe_unavailability(self):
        api_error = type(
            "BadRequestError",
            (Exception,),
            {
                "status_code": 400,
                "body": {"error": {"code": 400, "message": "private provider message"}},
            },
        )("private provider message")
        client = Mock()
        client.models.generate_content.side_effect = api_error

        result = generate_career_explanation(
            explanation_context(),
            client_factory=Mock(return_value=client),
        )

        self.assertEqual(
            result.diagnostic,
            "Phase: request execution; BadRequestError; "
            "model=gemini-3.8-flash; Google API HTTP 400; provider status unavailable",
        )
        self.assertNotIn("private", result.diagnostic)

    def test_structured_error_code_from_details_is_safely_reported(self):
        api_key = "test-only-key"
        raw_message = f"private provider message containing {api_key}"
        api_error = type(
            "BadRequestError",
            (Exception,),
            {
                "status_code": 400,
                "details": {
                    "error": {
                        "code": "https://api.example/errors/INVALID_ARGUMENT",
                        "message": raw_message,
                    }
                },
            },
        )(raw_message)
        client = Mock()
        client.models.generate_content.side_effect = api_error

        with self.assertLogs("gemini_service", level="WARNING") as captured:
            result = generate_career_explanation(
                explanation_context(),
                client_factory=Mock(return_value=client),
            )

        self.assertEqual(
            result.diagnostic,
            "Phase: request execution; BadRequestError; "
            "model=gemini-3.8-flash; Google API HTTP 400 (INVALID_ARGUMENT)",
        )
        for surfaced_text in (result.message, result.diagnostic, "\n".join(captured.output)):
            self.assertNotIn(raw_message, surfaced_text)
            self.assertNotIn(api_key, surfaced_text)

    def test_allowlisted_sdk_error_info_and_effective_model_are_reported(self):
        api_error = ClientError(
            400,
            {
                "error": {
                    "status": "INVALID_ARGUMENT",
                    "message": "private provider message",
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                            "reason": "MODEL_NOT_FOUND",
                            "domain": "private.provider.example",
                            "metadata": {"request": "private request data"},
                        }
                    ],
                }
            },
        )
        client = Mock()
        client.models.generate_content.side_effect = api_error

        with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-test-model"}):
            with self.assertLogs("gemini_service", level="WARNING") as captured:
                result = generate_career_explanation(
                    explanation_context(),
                    client_factory=Mock(return_value=client),
                )

        self.assertEqual(result.status, GeminiStatus.BAD_REQUEST)
        self.assertEqual(
            result.diagnostic,
            "Phase: request execution; ClientError; model=gemini-test-model; "
            "Google API HTTP 400 (INVALID_ARGUMENT); "
            "provider_error=MODEL_NOT_FOUND",
        )
        self.assertEqual(
            client.models.generate_content.call_args.kwargs["model"],
            "gemini-test-model",
        )
        surfaced_text = "\n".join(
            (result.message, result.diagnostic, *captured.output)
        )
        for private_value in (
            "private provider message",
            "private.provider.example",
            "private request data",
        ):
            self.assertNotIn(private_value, surfaced_text)

    def test_structured_bad_request_field_paths_are_reported_without_descriptions(self):
        private_text = "sensitive-looking description with private data"
        api_error = ClientError(
            400,
            {
                "error": {
                    "status": "INVALID_ARGUMENT",
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.BadRequest",
                            "fieldViolations": [
                                {
                                    "field": "contents[0].parts[0].text",
                                    "description": private_text,
                                },
                                {
                                    "field": "generationConfig.temperature",
                                    "description": f"API key {private_text}",
                                },
                            ],
                        }
                    ],
                }
            },
        )
        client = Mock()
        client.models.generate_content.side_effect = api_error

        with self.assertLogs("gemini_service", level="WARNING") as captured:
            result = generate_career_explanation(
                explanation_context(),
                client_factory=Mock(return_value=client),
            )

        expected_fields = (
            "invalid_fields=contents[0].parts[0].text,"
            "generationConfig.temperature"
        )
        self.assertIn(expected_fields, result.diagnostic)
        surfaced_text = "\n".join(
            (result.message, result.diagnostic, *captured.output)
        )
        self.assertNotIn(private_text, surfaced_text)
        self.assertNotIn("API key", surfaced_text)
        self.assertNotIn("fieldViolations", surfaced_text)

    def test_missing_structured_bad_request_details_keep_generic_diagnostic(self):
        api_error = ClientError(
            400,
            {"error": {"status": "INVALID_ARGUMENT", "message": "private detail"}},
        )
        client = Mock()
        client.models.generate_content.side_effect = api_error

        result = generate_career_explanation(
            explanation_context(),
            client_factory=Mock(return_value=client),
        )

        self.assertEqual(
            result.diagnostic,
            "Phase: request execution; ClientError; "
            "model=gemini-3.8-flash; Google API HTTP 400 (INVALID_ARGUMENT)",
        )
        self.assertNotIn("private detail", result.diagnostic)
        self.assertNotIn("invalid_fields=", result.diagnostic)

    def test_malformed_structured_bad_request_field_paths_are_not_reported(self):
        malformed_paths = (
            "contents[0].parts[0].text;api_key=secret",
            "../headers/Authorization",
            "field\nwith-newline",
            "x" * 161,
        )
        for field_path in malformed_paths:
            with self.subTest(field_path=field_path[:24]):
                api_error = ClientError(
                    400,
                    {
                        "error": {
                            "status": "INVALID_ARGUMENT",
                            "details": [
                                {
                                    "@type": "type.googleapis.com/google.rpc.BadRequest",
                                    "fieldViolations": [
                                        {"field": field_path, "description": "private"}
                                    ],
                                }
                            ],
                        }
                    },
                )
                client = Mock()
                client.models.generate_content.side_effect = api_error

                result = generate_career_explanation(
                    explanation_context(),
                    client_factory=Mock(return_value=client),
                )

                self.assertEqual(
                    result.diagnostic,
                    "Phase: request execution; ClientError; "
                    "model=gemini-3.8-flash; Google API HTTP 400 (INVALID_ARGUMENT)",
                )
                self.assertNotIn(field_path, result.diagnostic)
                self.assertNotIn("private", result.diagnostic)
                self.assertNotIn("invalid_fields=", result.diagnostic)

    def test_malformed_or_unallowlisted_error_details_are_not_reported(self):
        malformed_details = (
            "private raw response",
            ["unexpected response list"],
            {"error": "not a structured error"},
            {"error": {"details": "MODEL_NOT_FOUND"}},
            {
                "error": {
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                            "reason": "PRIVATE_PROVIDER_VALUE",
                        }
                    ]
                }
            },
        )
        for details in malformed_details:
            with self.subTest(details_type=type(details).__name__):
                api_error = type(
                    "BadRequestError",
                    (Exception,),
                    {"code": 400, "details": details},
                )("private exception text")
                client = Mock()
                client.models.generate_content.side_effect = api_error

                result = generate_career_explanation(
                    explanation_context(),
                    client_factory=Mock(return_value=client),
                )

                self.assertEqual(
                    result.diagnostic,
                    "Phase: request execution; BadRequestError; "
                    "model=gemini-3.8-flash; Google API HTTP 400; "
                    "provider status unavailable",
                )
                self.assertNotIn("private", result.diagnostic)
                self.assertNotIn("PRIVATE_PROVIDER_VALUE", result.diagnostic)
                self.assertNotIn("MODEL_NOT_FOUND", result.diagnostic)

    def test_error_details_property_failure_is_handled_without_leaking_text(self):
        class UnexpectedDetailsError(Exception):
            code = 400

            @property
            def details(self):
                raise ValueError("private provider response")

        client = Mock()
        client.models.generate_content.side_effect = UnexpectedDetailsError(
            "private exception text"
        )

        with self.assertLogs("gemini_service", level="WARNING") as captured:
            result = generate_career_explanation(
                explanation_context(),
                client_factory=Mock(return_value=client),
            )

        self.assertEqual(
            result.diagnostic,
            "Phase: request execution; UnexpectedDetailsError; "
            "model=gemini-3.8-flash; Google API HTTP 400; "
            "provider status unavailable",
        )
        self.assertNotIn("private", result.diagnostic)
        self.assertNotIn("private", "\n".join(captured.output))

    def test_model_that_could_be_a_credential_is_hidden_from_diagnostic(self):
        api_error = type(
            "BadRequestError",
            (Exception,),
            {
                "code": 400,
                "details": {
                    "error": {
                        "details": [
                            {
                                "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                                "reason": "MODEL_NOT_FOUND",
                            }
                        ]
                    }
                },
            },
        )("private exception text")
        client = Mock()
        client.models.generate_content.side_effect = api_error

        with patch.dict(os.environ, {"GEMINI_MODEL": "test-only-key"}):
            with self.assertLogs("gemini_service", level="WARNING") as captured:
                result = generate_career_explanation(
                    explanation_context(),
                    client_factory=Mock(return_value=client),
                )

        self.assertIn("model=unavailable", result.diagnostic)
        self.assertNotIn("test-only-key", result.diagnostic)
        self.assertNotIn("private", "\n".join(captured.output))

    def test_invalid_structured_error_code_from_details_is_not_reported(self):
        api_key = "test-only-key"
        invalid_code = "https://api.example/errors/INVALID-ARGUMENT\nprivate"
        raw_message = f"private provider message containing {api_key}"
        api_error = type(
            "BadRequestError",
            (Exception,),
            {
                "status_code": 400,
                "details": {
                    "error": {
                        "code": invalid_code,
                        "message": raw_message,
                    }
                },
            },
        )(raw_message)
        client = Mock()
        client.models.generate_content.side_effect = api_error

        with self.assertLogs("gemini_service", level="WARNING") as captured:
            result = generate_career_explanation(
                explanation_context(),
                client_factory=Mock(return_value=client),
            )

        self.assertEqual(
            result.diagnostic,
            "Phase: request execution; BadRequestError; "
            "model=gemini-3.8-flash; Google API HTTP 400; provider status unavailable",
        )
        for surfaced_text in (result.message, result.diagnostic, "\n".join(captured.output)):
            self.assertNotIn(invalid_code, surfaced_text)
            self.assertNotIn("INVALID-ARGUMENT", surfaced_text)
            self.assertNotIn(raw_message, surfaced_text)
            self.assertNotIn(api_key, surfaced_text)

    def test_request_bad_request_reports_missing_provider_status(self):
        api_error = type(
            "BadRequestError",
            (Exception,),
            {"code": 400, "status": None},
        )("private provider message")
        client = Mock()
        client.models.generate_content.side_effect = api_error

        result = generate_career_explanation(
            explanation_context(),
            client_factory=Mock(return_value=client),
        )

        self.assertEqual(
            result.diagnostic,
            "Phase: request execution; BadRequestError; "
            "model=gemini-3.8-flash; Google API HTTP 400; provider status unavailable",
        )
        self.assertNotIn("private", result.diagnostic)

    def test_unsafe_provider_status_is_not_included_in_diagnostic(self):
        api_error = type(
            "BadRequestError",
            (Exception,),
            {"code": 400, "status": "INVALID-ARGUMENT\nprivate"},
        )("private provider message")
        client = Mock()
        client.models.generate_content.side_effect = api_error

        result = generate_career_explanation(
            explanation_context(),
            client_factory=Mock(return_value=client),
        )

        self.assertEqual(
            result.diagnostic,
            "Phase: request execution; BadRequestError; "
            "model=gemini-3.8-flash; Google API HTTP 400; "
            "provider status unavailable",
        )
        self.assertNotIn("INVALID-ARGUMENT", result.diagnostic)
        self.assertNotIn("private", result.diagnostic)

    def test_request_error_without_structured_metadata_reports_unknown_reason(self):
        api_error = type("BadRequestError", (Exception,), {})(
            "private provider message"
        )
        client = Mock()
        client.models.generate_content.side_effect = api_error

        result = generate_career_explanation(
            explanation_context(),
            client_factory=Mock(return_value=client),
        )

        self.assertEqual(
            result.diagnostic,
            "Phase: request execution; BadRequestError; "
            "model=gemini-3.8-flash; provider reason unavailable",
        )

    def test_import_error_identifies_missing_module_without_raw_error_text(self):
        import_error = ImportError("private detail must not be shown")
        import_error.name = "google.genai.optional_module"

        result = generate_career_explanation(
            explanation_context(),
            client_factory=Mock(side_effect=import_error),
        )

        self.assertEqual(result.status, GeminiStatus.SDK_UNAVAILABLE)
        self.assertEqual(
            result.diagnostic,
            "Phase: client initialization; ImportError; "
            "missing module: google.genai.optional_module",
        )
        self.assertNotIn("private", result.diagnostic)

    def test_import_error_identifies_missing_symbol_without_raw_error_text(self):
        import_error = ImportError(
            "cannot import name 'UnavailableClient' from 'google.genai' "
            "(private path)"
        )

        result = generate_career_explanation(
            explanation_context(),
            client_factory=Mock(side_effect=import_error),
        )

        self.assertEqual(result.status, GeminiStatus.SDK_UNAVAILABLE)
        self.assertEqual(
            result.diagnostic,
            "Phase: client initialization; ImportError; "
            "missing symbol: UnavailableClient from google.genai",
        )
        self.assertNotIn("private path", result.diagnostic)

    def test_request_import_error_identifies_request_execution_phase(self):
        client = Mock()
        import_error = ImportError("request transport module not found")
        import_error.name = "google.genai.request_transport"
        client.models.generate_content.side_effect = import_error

        result = generate_career_explanation(
            explanation_context(),
            client_factory=Mock(return_value=client),
        )

        self.assertEqual(result.status, GeminiStatus.SDK_UNAVAILABLE)
        self.assertEqual(
            result.diagnostic,
            "Phase: request execution; ImportError; "
            "model=gemini-3.8-flash; missing module: google.genai.request_transport",
        )

    def test_unexpected_response_format_is_reported(self):
        client = Mock()
        client.models.generate_content.return_value = object()

        result = generate_career_explanation(
            explanation_context(),
            client_factory=Mock(return_value=client),
        )

        self.assertEqual(result.status, GeminiStatus.INVALID_RESPONSE)

    def test_timeout_and_rate_limit_have_user_friendly_status(self):
        for error, expected_status in (
            (TimeoutError("private timeout details"), GeminiStatus.TIMEOUT),
            (
                type(
                    "APIError",
                    (Exception,),
                    {"code": 429, "status": "RESOURCE_EXHAUSTED"},
                )("private quota details"),
                GeminiStatus.RATE_LIMITED,
            ),
        ):
            with self.subTest(status=expected_status):
                result = generate_career_explanation(
                    explanation_context(),
                    client_factory=Mock(side_effect=error),
                )

                self.assertEqual(result.status, expected_status)
                self.assertNotIn("private", result.message)

    def test_request_timeout_is_classified_without_exposing_exception_details(self):
        client = Mock()
        client.models.generate_content.side_effect = TimeoutError(
            "private request timeout details"
        )

        with patch("gemini_service.time.sleep") as sleep, self.assertLogs(
            "gemini_service",
            level="WARNING",
        ) as captured:
            result = generate_career_explanation(
                explanation_context(),
                client_factory=Mock(return_value=client),
            )

        self.assertEqual(result.status, GeminiStatus.TIMEOUT)
        self.assertNotIn("private", result.message)
        self.assertNotIn("private", result.diagnostic)
        self.assertNotIn("private", "\n".join(captured.output))
        self.assertEqual(client.models.generate_content.call_count, 2)
        sleep.assert_called_once()
        self.assertEqual(
            client.models.generate_content.call_args.kwargs["config"],
            {
                "http_options": {"timeout": GEMINI_REQUEST_TIMEOUT_MS},
                "max_output_tokens": GEMINI_MAX_OUTPUT_TOKENS,
                "thinking_config": {
                    "thinking_level": GEMINI_THINKING_LEVEL,
                },
            },
        )

    def test_transient_http_failures_retry_once_and_can_succeed(self):
        transient_errors = (
            (429, "RESOURCE_EXHAUSTED"),
            (500, "INTERNAL"),
            (502, "UNAVAILABLE"),
            (503, "UNAVAILABLE"),
            (504, "DEADLINE_EXCEEDED"),
        )
        for status_code, api_status in transient_errors:
            with self.subTest(status_code=status_code):
                client = Mock()
                api_error = type(
                    "TransientAPIError",
                    (Exception,),
                    {"code": status_code, "status": api_status},
                )("private transient provider response")
                client.models.generate_content.side_effect = [
                    api_error,
                    SimpleNamespace(text="Recovered explanation."),
                ]

                with patch("gemini_service.time.sleep") as sleep:
                    result = generate_career_explanation(
                        explanation_context(),
                        client_factory=Mock(return_value=client),
                    )

                self.assertEqual(result.status, GeminiStatus.SUCCESS)
                self.assertEqual(result.text, "Recovered explanation.")
                self.assertEqual(client.models.generate_content.call_count, 2)
                sleep.assert_called_once()

    def test_transient_http_failure_on_both_attempts_returns_safe_failure(self):
        api_key = "test-only-key"
        raw_message = f"private provider response containing {api_key}"
        api_error = type(
            "DeadlineExceededError",
            (Exception,),
            {"code": 504, "status": "DEADLINE_EXCEEDED"},
        )(raw_message)
        client = Mock()
        client.models.generate_content.side_effect = api_error

        with patch("gemini_service.time.sleep") as sleep, self.assertLogs(
            "gemini_service",
            level="WARNING",
        ) as captured:
            result = generate_career_explanation(
                explanation_context(),
                client_factory=Mock(return_value=client),
            )

        self.assertEqual(result.status, GeminiStatus.TIMEOUT)
        self.assertEqual(client.models.generate_content.call_count, 2)
        sleep.assert_called_once()
        self.assertEqual(
            result.diagnostic,
            "Phase: request execution; DeadlineExceededError; "
            "model=gemini-3.8-flash; Google API HTTP 504 (DEADLINE_EXCEEDED)",
        )
        for surfaced_text in (
            result.message,
            result.diagnostic,
            "\n".join(captured.output),
        ):
            self.assertNotIn(raw_message, surfaced_text)
            self.assertNotIn(api_key, surfaced_text)

    def test_permanent_http_failure_does_not_retry(self):
        permanent_errors = (
            (400, "INVALID_ARGUMENT", GeminiStatus.BAD_REQUEST),
            (401, "UNAUTHENTICATED", GeminiStatus.INVALID_API_KEY),
            (403, "PERMISSION_DENIED", GeminiStatus.PERMISSION_ERROR),
            (404, "NOT_FOUND", GeminiStatus.MODEL_UNAVAILABLE),
        )
        for status_code, api_status, expected_status in permanent_errors:
            with self.subTest(status_code=status_code):
                api_error = type(
                    "PermanentAPIError",
                    (Exception,),
                    {"code": status_code, "status": api_status},
                )("private permanent provider details")
                client = Mock()
                client.models.generate_content.side_effect = api_error

                with patch("gemini_service.time.sleep") as sleep:
                    result = generate_career_explanation(
                        explanation_context(),
                        client_factory=Mock(return_value=client),
                    )

                self.assertEqual(result.status, expected_status)
                client.models.generate_content.assert_called_once()
                sleep.assert_not_called()
                self.assertNotIn("private", result.diagnostic)

    def test_transient_connection_error_retries_once(self):
        client = Mock()
        client.models.generate_content.side_effect = [
            ConnectionError("private connection details"),
            SimpleNamespace(text="Recovered explanation."),
        ]

        with patch("gemini_service.time.sleep") as sleep:
            result = generate_career_explanation(
                explanation_context(),
                client_factory=Mock(return_value=client),
            )

        self.assertEqual(result.status, GeminiStatus.SUCCESS)
        self.assertEqual(client.models.generate_content.call_count, 2)
        sleep.assert_called_once()

    def test_network_failure_is_reported_without_provider_details(self):
        result = generate_career_explanation(
            explanation_context(),
            client_factory=Mock(side_effect=ConnectionError("private network details")),
        )

        self.assertEqual(result.status, GeminiStatus.NETWORK_ERROR)
        self.assertNotIn("private", result.message)

    def test_missing_sdk_is_reported_without_crashing(self):
        result = generate_career_explanation(
            explanation_context(),
            client_factory=Mock(side_effect=ModuleNotFoundError("google.genai")),
        )

        self.assertEqual(result.status, GeminiStatus.SDK_UNAVAILABLE)

    def test_gemini_does_not_change_deterministic_scores_or_order(self):
        before = rank_careers(CAREERS, ["Python", "SQL"], ["Data Science"])
        client = Mock()
        client.models.generate_content.return_value = SimpleNamespace(
            text="Supplementary suggestion."
        )
        result = generate_career_explanation(
            explanation_context(),
            client_factory=Mock(return_value=client),
        )
        after = rank_careers(CAREERS, ["Python", "SQL"], ["Data Science"])

        self.assertTrue(result.succeeded)
        self.assertEqual(
            [(item.career_id, item.score) for item in before],
            [(item.career_id, item.score) for item in after],
        )

    def test_failed_gemini_explanation_does_not_change_recommendations(self):
        before = rank_careers(CAREERS, ["Python", "SQL"], ["Data Science"])
        client = Mock()
        client.models.generate_content.side_effect = type(
            "DeadlineExceededError",
            (Exception,),
            {"code": 504, "status": "DEADLINE_EXCEEDED"},
        )("private provider response")

        with patch("gemini_service.time.sleep"):
            result = generate_career_explanation(
                explanation_context(),
                client_factory=Mock(return_value=client),
            )
        after = rank_careers(CAREERS, ["Python", "SQL"], ["Data Science"])

        self.assertEqual(result.status, GeminiStatus.TIMEOUT)
        self.assertEqual(client.models.generate_content.call_count, 2)
        self.assertIn("Data Scientist", result.fallback_text)
        self.assertIn("Python", result.fallback_text)
        self.assertEqual(
            [(item.career_id, item.score) for item in before],
            [(item.career_id, item.score) for item in after],
        )

    def test_existing_no_match_results_are_not_meaningful(self):
        ranked = rank_careers(CAREERS, ["C++"], ["Gaming"])

        self.assertFalse(has_meaningful_career_match(ranked))
        self.assertTrue(all(item.score == 0 for item in ranked))

    def test_results_page_preserves_no_match_view_without_ai_controls(self):
        app = AppTest.from_file(APP_PATH).run(timeout=20)
        app.session_state["page"] = "Results"
        app.session_state["signed_in"] = True
        app.session_state["profile"] = {
            "name": "Test Student",
            "confirmed_skills": ["C++"],
            "confirmed_interests": ["Gaming"],
        }
        app.run(timeout=20)

        self.assertEqual(len(app.exception), 0)
        self.assertTrue(
            any("No strong match can be identified" in warning.value for warning in app.warning)
        )
        self.assertFalse(
            any(button.label == "Generate AI Career Explanation" for button in app.button)
        )

    def test_local_ai_explanation_is_requested_only_after_button_click(self):
        app = AppTest.from_file(APP_PATH).run(timeout=20)
        app.session_state["page"] = "Results"
        app.session_state["signed_in"] = True
        app.session_state["profile"] = {
            "name": "Test Student",
            "confirmed_skills": ["Python"],
            "confirmed_interests": ["Data Science"],
        }
        mocked_result = LocalExplanationResult(
            LocalExplanationStatus.SUCCESS,
            text="Supplementary local learning suggestion.",
        )
        expected_recommendation = next(
            recommendation
            for recommendation in rank_careers(
                CAREERS,
                ["Python"],
                ["Data Science"],
            )
            if recommendation.career_id == "data-scientist"
        )

        with patch(
            "ollama_explanation_service.generate_local_career_explanation",
            return_value=mocked_result,
        ) as generate:
            app.run(timeout=20)
            self.assertEqual(len(app.exception), 0)
            generate.assert_not_called()
            button = next(item for item in app.button if item.key == "generate_ai_data-scientist")
            button.click().run(timeout=20)

        self.assertEqual(len(app.exception), 0)
        generate.assert_called_once()
        self.assertEqual(
            app.session_state["career_explanations"]["data-scientist"].text,
            "Supplementary local learning suggestion.",
        )
        self.assertIsInstance(generate.call_args.args[0], LocalExplanationContext)
        self.assertEqual(
            generate.call_args.args[0],
            LocalExplanationContext(
                career_name="Data Scientist",
                matched_skills=expected_recommendation.matched_skills,
                missing_skills=expected_recommendation.missing_skills,
                interests=expected_recommendation.matched_interests,
                recommendation_score=expected_recommendation.score,
            ),
        )
        self.assertTrue(
            any(
                f"Heuristic relevance: {expected_recommendation.score:.1f}/100"
                in item.value
                for item in app.markdown
            )
        )
        self.assertTrue(
            any(
                "Matched 1 of 5 required skills and 1 of 2 interest tags"
                in item.value
                for item in app.markdown
            )
        )
        self.assertFalse(
            any("Rule-based career explanation" in item.value for item in app.markdown)
        )

    def test_local_provider_failure_shows_rule_based_fallback_without_crashing_results(self):
        app = AppTest.from_file(APP_PATH).run(timeout=20)
        app.session_state["page"] = "Results"
        app.session_state["signed_in"] = True
        app.session_state["profile"] = {
            "name": "Test Student",
            "confirmed_skills": ["Python"],
            "confirmed_interests": ["Data Science"],
        }
        failure = LocalExplanationResult(
            LocalExplanationStatus.UNAVAILABLE,
            diagnostic="category=unavailable",
            fallback_text=(
                "For Data Scientist, your assessment matches Python and Data Science. "
                "This rule-based explanation is not AI-generated."
            ),
        )

        with patch(
            "ollama_explanation_service.generate_local_career_explanation",
            return_value=failure,
        ) as generate:
            app.run(timeout=20)
            next(
                item for item in app.button
                if item.key == "generate_ai_data-scientist"
            ).click().run(timeout=20)

        self.assertEqual(len(app.exception), 0)
        generate.assert_called_once()
        self.assertTrue(any(failure.message in item.value for item in app.info))
        self.assertTrue(
            any(
                "Rule-based career explanation (not AI-generated)" in item.value
                for item in app.markdown
            )
        )
        self.assertTrue(
            any("For Data Scientist" in item.value for item in app.markdown)
        )
        self.assertTrue(
            any(failure.diagnostic in item.value for item in app.caption)
        )
        self.assertTrue(
            any(
                "Matched 1 of 5 required skills and 1 of 2 interest tags"
                in item.value
                for item in app.markdown
            )
        )


if __name__ == "__main__":
    unittest.main()
