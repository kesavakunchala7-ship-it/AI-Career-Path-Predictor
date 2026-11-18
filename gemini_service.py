"""Optional Gemini-generated explanations for deterministic career matches."""

import logging
import os
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol

import streamlit as st

DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_REQUEST_TIMEOUT_MS = 30_000
GEMINI_MAX_OUTPUT_TOKENS = 512
GEMINI_THINKING_LEVEL = "LOW"
GEMINI_MAX_REQUEST_ATTEMPTS = 2
GEMINI_RETRY_BACKOFF_SECONDS = 0.5
_RETRYABLE_HTTP_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
_TRANSIENT_NETWORK_ERROR_NAMES = frozenset(
    {
        "connecterror",
        "connecttimeout",
        "networkerror",
        "pooltimeout",
        "readerror",
        "readtimeout",
        "remoteprotocolerror",
        "writeerror",
        "writetimeout",
    }
)
logger = logging.getLogger(__name__)


class GeminiStatus(str, Enum):
    SUCCESS = "success"
    MISSING_CONFIG = "missing_config"
    INVALID_API_KEY = "invalid_api_key"
    PERMISSION_ERROR = "permission_error"
    MODEL_UNAVAILABLE = "model_unavailable"
    BAD_REQUEST = "bad_request"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    SDK_UNAVAILABLE = "sdk_unavailable"
    SERVICE_ERROR = "service_error"
    EMPTY_RESPONSE = "empty_response"
    INVALID_RESPONSE = "invalid_response"


@dataclass(frozen=True)
class GeminiExplanationResult:
    status: GeminiStatus
    text: str = ""
    diagnostic: str = ""
    fallback_text: str = ""

    @property
    def succeeded(self) -> bool:
        return self.status is GeminiStatus.SUCCESS

    @property
    def message(self) -> str:
        return _STATUS_MESSAGES[self.status]


@dataclass(frozen=True)
class CareerExplanationContext:
    career_title: str
    career_description: str
    career_skills: tuple[str, ...]
    career_interests: tuple[str, ...]
    roadmap: tuple[str, ...]
    confirmed_skills: tuple[str, ...]
    confirmed_interests: tuple[str, ...]
    matched_skills: tuple[str, ...]
    matched_interests: tuple[str, ...]
    missing_skills: tuple[str, ...]
    suggested_skills: tuple[str, ...]


class _Models(Protocol):
    def generate_content(
        self,
        *,
        model: str,
        contents: str,
        config: Mapping[str, object],
    ) -> object: ...


class _GeminiClient(Protocol):
    models: _Models


_STATUS_MESSAGES = {
    GeminiStatus.SUCCESS: "",
    GeminiStatus.MISSING_CONFIG: (
        "AI explanations are not configured. Set GEMINI_API_KEY to enable this optional feature."
    ),
    GeminiStatus.INVALID_API_KEY: (
        "Gemini rejected the API key. Check the GEMINI_API_KEY configuration and try again."
    ),
    GeminiStatus.PERMISSION_ERROR: (
        "The API key or Google project may not have permission to use Gemini. Check the key's API restrictions and project configuration."
    ),
    GeminiStatus.MODEL_UNAVAILABLE: (
        "The configured Gemini model was not found or is unavailable to this project. Check GEMINI_MODEL and model access."
    ),
    GeminiStatus.BAD_REQUEST: (
        "Gemini did not accept the explanation request. Your recommendation is unchanged; review the request configuration before trying again."
    ),
    GeminiStatus.RATE_LIMITED: (
        "Gemini is temporarily rate limited. Wait a moment and try again."
    ),
    GeminiStatus.TIMEOUT: (
        "Gemini did not respond in time. Your recommendation is unchanged; try again later."
    ),
    GeminiStatus.NETWORK_ERROR: (
        "Gemini could not be reached. Your recommendation is unchanged; check the connection and try again."
    ),
    GeminiStatus.SDK_UNAVAILABLE: (
        "The Gemini SDK is unavailable. Install the project requirements to enable AI explanations."
    ),
    GeminiStatus.SERVICE_ERROR: (
        "Gemini is temporarily unavailable. Your recommendation is unchanged; try again later."
    ),
    GeminiStatus.EMPTY_RESPONSE: (
        "Gemini returned an empty explanation. Your recommendation is unchanged; try again."
    ),
    GeminiStatus.INVALID_RESPONSE: (
        "Gemini returned an unexpected response. Your recommendation is unchanged; try again."
    ),
}
_MISSING_RESPONSE_TEXT = object()
_API_STATUS_IDENTIFIERS = frozenset(
    {
        "ABORTED",
        "ALREADY_EXISTS",
        "CANCELLED",
        "DATA_LOSS",
        "DEADLINE_EXCEEDED",
        "FAILED_PRECONDITION",
        "INTERNAL",
        "INVALID_ARGUMENT",
        "NOT_FOUND",
        "OUT_OF_RANGE",
        "PERMISSION_DENIED",
        "RESOURCE_EXHAUSTED",
        "UNAUTHENTICATED",
        "UNAVAILABLE",
        "UNIMPLEMENTED",
        "UNKNOWN",
    }
)
_PROVIDER_ERROR_IDENTIFIERS = frozenset(
    {
        "API_KEY_ANDROID_APP_BLOCKED",
        "API_KEY_INVALID",
        "API_KEY_IP_ADDRESS_BLOCKED",
        "API_KEY_IOS_APP_BLOCKED",
        "API_KEY_SERVICE_BLOCKED",
        "API_KEY_HTTP_REFERRER_BLOCKED",
        "BILLING_DISABLED",
        "CONSUMER_INVALID",
        "CONSUMER_SUSPENDED",
        "MODEL_NOT_FOUND",
        "MODEL_UNAVAILABLE",
        "QUOTA_EXCEEDED",
        "RATE_LIMIT_EXCEEDED",
        "SERVICE_DISABLED",
        "USER_LOCATION_UNSUPPORTED",
    }
)
_BAD_REQUEST_FIELD_PATH_PATTERN = re.compile(
    r"[A-Za-z][A-Za-z0-9_]*(?:\[[0-9]{1,6}\])?"
    r"(?:\.[A-Za-z][A-Za-z0-9_]*(?:\[[0-9]{1,6}\])?)*"
)
_MAX_BAD_REQUEST_FIELD_PATH_LENGTH = 160
_MAX_BAD_REQUEST_FIELD_PATHS = 5
_SAFE_PROVIDER_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}")


def _safe_attribute(value: object, name: str) -> object:
    try:
        return getattr(value, name, None)
    except Exception:
        return None


def _safe_mapping_value(value: Mapping[object, object], key: str) -> object:
    try:
        return value.get(key)
    except Exception:
        return None


def _allowlisted_status(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    if value in _API_STATUS_IDENTIFIERS:
        return value
    if "/" in value:
        suffix = value.rstrip("/").rsplit("/", 1)[-1]
        if suffix in _API_STATUS_IDENTIFIERS:
            return suffix
    return None


def _safe_provider_error_identifier(error: Exception) -> str | None:
    details = _safe_attribute(error, "details")
    if not isinstance(details, Mapping):
        return None

    nested_error = _safe_mapping_value(details, "error")
    if not isinstance(nested_error, Mapping):
        nested_error = details

    reason = _safe_mapping_value(nested_error, "reason")
    if isinstance(reason, str) and reason in _PROVIDER_ERROR_IDENTIFIERS:
        return reason

    structured_details = _safe_mapping_value(nested_error, "details")
    if not isinstance(structured_details, (list, tuple)):
        return None
    for detail in structured_details:
        if not isinstance(detail, Mapping):
            continue
        detail_type = _safe_mapping_value(detail, "@type")
        if detail_type != "type.googleapis.com/google.rpc.ErrorInfo":
            continue
        reason = _safe_mapping_value(detail, "reason")
        if isinstance(reason, str) and reason in _PROVIDER_ERROR_IDENTIFIERS:
            return reason
    return None


def _safe_bad_request_field_paths(error: Exception) -> tuple[str, ...] | None:
    details = _safe_attribute(error, "details")
    if not isinstance(details, Mapping):
        return None

    nested_error = _safe_mapping_value(details, "error")
    if not isinstance(nested_error, Mapping):
        nested_error = details
    structured_details = _safe_mapping_value(nested_error, "details")
    if not isinstance(structured_details, (list, tuple)):
        return None

    for detail in structured_details:
        if not isinstance(detail, Mapping):
            continue
        detail_type = _safe_mapping_value(detail, "@type")
        if detail_type != "type.googleapis.com/google.rpc.BadRequest":
            continue

        violations = _safe_mapping_value(detail, "fieldViolations")
        if not isinstance(violations, (list, tuple)) or not violations:
            return None

        paths: list[str] = []
        for violation in violations:
            if not isinstance(violation, Mapping):
                return None
            field_path = _safe_mapping_value(violation, "field")
            if (
                not isinstance(field_path, str)
                or len(field_path) > _MAX_BAD_REQUEST_FIELD_PATH_LENGTH
                or _BAD_REQUEST_FIELD_PATH_PATTERN.fullmatch(field_path) is None
            ):
                return None
            if field_path not in paths:
                paths.append(field_path)
            if len(paths) > _MAX_BAD_REQUEST_FIELD_PATHS:
                return None

        return tuple(paths) or None
    return None


def _safe_model_identifier(model: object, api_key: str) -> str:
    if (
        not isinstance(model, str)
        or api_key in model
        or model.startswith("AIza")
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}", model)
    ):
        return "unavailable"
    return model


def _read_streamlit_api_key() -> object:
    try:
        return st.secrets["GEMINI_API_KEY"]
    except (KeyError, FileNotFoundError):
        return None


def _configured_api_key() -> str | None:
    environment_key = os.getenv("GEMINI_API_KEY")
    if isinstance(environment_key, str) and environment_key.strip():
        return environment_key.strip()

    secret_key = _read_streamlit_api_key()
    if isinstance(secret_key, str) and secret_key.strip():
        return secret_key.strip()
    return None


def _configured_model() -> str:
    configured_model = os.getenv("GEMINI_MODEL")
    return configured_model.strip() if configured_model and configured_model.strip() else DEFAULT_GEMINI_MODEL


def _create_client(api_key: str) -> _GeminiClient:
    from google import genai

    return genai.Client(api_key=api_key)


def _format_items(items: tuple[str, ...]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- None provided"


def _build_prompt(context: CareerExplanationContext) -> str:
    return f"""Write a concise, supportive supplementary explanation for a student's exploration of this career.

Use only the supplied career-catalog details and assessment data for career-specific facts. Explain relevant confirmed skills and interests, note skill gaps, suggest learning topics, and connect suggestions to the supplied roadmap. Do not invent salary, employment statistics, job-market demand, certifications, job-placement claims, or guaranteed outcomes. Do not describe this as a professional career assessment. Clearly present guidance as suggestions, not verified facts.

Career from the project catalog: {context.career_title}
Catalog description: {context.career_description}
Catalog skill tags:
{_format_items(context.career_skills)}
Catalog interest tags:
{_format_items(context.career_interests)}
Illustrative catalog roadmap:
{_format_items(context.roadmap)}
Student-confirmed skills:
{_format_items(context.confirmed_skills)}
Student-confirmed interests:
{_format_items(context.confirmed_interests)}
Matched catalog skills:
{_format_items(context.matched_skills)}
Matched catalog interests:
{_format_items(context.matched_interests)}
Required skills not confirmed:
{_format_items(context.missing_skills)}
Additional catalog skills suggested for exploration:
{_format_items(context.suggested_skills)}
"""


def _build_fallback_explanation(context: CareerExplanationContext) -> str:
    matched = ", ".join(context.matched_skills) or "no listed skills"
    interests = ", ".join(context.matched_interests) or "no listed interests"
    gaps = ", ".join(context.missing_skills) or "no unconfirmed required skills"
    suggestions = ", ".join(context.suggested_skills) or "the career's listed skills"
    roadmap_step = context.roadmap[0] if context.roadmap else (
        "Review the career's listed skills and choose one topic to explore."
    )
    return (
        f"For {context.career_title}, your assessment matches these listed skills: "
        f"{matched}; and interests: {interests}. Skills to build or confirm include "
        f"{gaps}. A useful next area to explore is {suggestions}. As a first step, "
        f"{roadmap_step} This is a local summary of your assessment and the project "
        "career catalog, not an AI-generated explanation or a prediction of career outcomes."
    )


def _safe_api_status(error: Exception) -> str | None:
    api_status = _allowlisted_status(_safe_attribute(error, "status"))
    if api_status is not None:
        return api_status

    for attribute in ("body", "details"):
        body = _safe_attribute(error, attribute)
        if not isinstance(body, Mapping):
            continue
        for container in (body, _safe_mapping_value(body, "error")):
            if not isinstance(container, Mapping):
                continue
            for field in ("status", "code"):
                api_status = _allowlisted_status(
                    _safe_mapping_value(container, field)
                )
                if api_status is not None:
                    return api_status
    return None


def _safe_http_code(error: Exception) -> int | None:
    for attribute in ("code", "status_code"):
        try:
            code = int(_safe_attribute(error, attribute))
        except (TypeError, ValueError):
            continue
        if 100 <= code <= 599:
            return code

    response = _safe_attribute(error, "response")
    try:
        code = int(_safe_attribute(response, "status_code"))
    except (TypeError, ValueError):
        return None
    return code if 100 <= code <= 599 else None


def _safe_provider_request_id(value: object, api_key: str) -> str | None:
    if (
        not isinstance(value, str)
        or not value
        or api_key and api_key in value
        or _SAFE_PROVIDER_ID_PATTERN.fullmatch(value) is None
    ):
        return None
    return value


def _provider_correlation_id(
    value: object,
    api_key: str,
) -> tuple[str, str] | None:
    response_id = _safe_provider_request_id(
        _safe_attribute(value, "response_id"),
        api_key,
    )
    if response_id is not None:
        return "provider_response_id", response_id

    sdk_response = _safe_attribute(value, "sdk_http_response")
    if sdk_response is None:
        sdk_response = _safe_attribute(value, "response")
    headers = _safe_attribute(sdk_response, "headers")
    if not isinstance(headers, Mapping):
        return None

    try:
        for name, header_value in headers.items():
            if (
                isinstance(name, str)
                and name.casefold() in {
                    "x-goog-request-id",
                    "x-request-id",
                    "request-id",
                }
            ):
                safe_value = _safe_provider_request_id(header_value, api_key)
                if safe_value is not None:
                    return "provider_request_id", safe_value
    except Exception:
        return None
    return None


def _log_request_attempt(
    *,
    started_at: datetime,
    started_counter: float,
    attempt: int,
    model: str,
    api_key: str,
    outcome: str,
    category: str,
    http_status: int | None,
    correlation_id: tuple[str, str] | None = None,
    diagnostic: str = "",
    retrying: bool = False,
) -> None:
    completed_at = datetime.now(timezone.utc)
    duration_ms = max(0, round((time.perf_counter() - started_counter) * 1000))
    safe_model = _safe_model_identifier(model, api_key)
    fields = (
        f"started_at={started_at.isoformat(timespec='milliseconds')}; "
        f"completed_at={completed_at.isoformat(timespec='milliseconds')}; "
        f"duration_ms={duration_ms}; attempt={attempt}; model={safe_model}; "
        f"outcome={outcome}; http_status={http_status if http_status is not None else 'unavailable'}; "
        f"category={category}"
    )
    if correlation_id is not None:
        fields += f"; {correlation_id[0]}={correlation_id[1]}"
    if diagnostic:
        fields += f"; diagnostic={diagnostic}"
    if retrying:
        fields += "; retrying=true"
    log = logger.info if outcome == "success" else logger.warning
    log("Gemini request attempt completed: %s", fields)


def _exception_status(error: Exception) -> GeminiStatus:
    if isinstance(error, ImportError):
        return GeminiStatus.SDK_UNAVAILABLE

    error_name = type(error).__name__.casefold()
    if "timeout" in error_name or isinstance(error, TimeoutError):
        return GeminiStatus.TIMEOUT
    if any(token in error_name for token in ("connection", "connect", "network", "transport")):
        return GeminiStatus.NETWORK_ERROR

    status_code = _safe_http_code(error)
    if status_code == 400:
        return GeminiStatus.BAD_REQUEST
    if status_code == 401:
        return GeminiStatus.INVALID_API_KEY
    if status_code == 403:
        return GeminiStatus.PERMISSION_ERROR
    if status_code == 404:
        return GeminiStatus.MODEL_UNAVAILABLE
    if status_code == 429:
        return GeminiStatus.RATE_LIMITED
    if status_code in (408, 504):
        return GeminiStatus.TIMEOUT
    return GeminiStatus.SERVICE_ERROR


def _is_retryable_request_error(error: Exception) -> bool:
    status_code = _safe_http_code(error)
    if status_code is not None:
        return status_code in _RETRYABLE_HTTP_STATUS_CODES

    return (
        isinstance(error, (ConnectionError, TimeoutError))
        or type(error).__name__.casefold() in _TRANSIENT_NETWORK_ERROR_NAMES
    )


def _safe_diagnostic(
    error: Exception,
    phase: str,
    *,
    model: str | None = None,
    api_key: str = "",
) -> str:
    exception_name = re.sub(r"[^A-Za-z0-9_]", "", type(error).__name__)[:48]
    prefix = f"Phase: {phase}; {exception_name or 'unknown error'}"
    if model is not None:
        prefix += f"; model={_safe_model_identifier(model, api_key)}"

    if isinstance(error, ImportError):
        missing_module = _safe_attribute(error, "name")
        if isinstance(missing_module, str):
            safe_module = re.fullmatch(
                r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*",
                missing_module,
            )
            if safe_module:
                return f"{prefix}; missing module: {safe_module.group(0)}"

        message = _safe_attribute(error, "msg")
        if isinstance(message, str):
            missing_import = re.search(
                r"cannot import name ['\"]([A-Za-z_]\w*)['\"] from ['\"]"
                r"([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)['\"]",
                message,
            )
            if missing_import:
                symbol, module = missing_import.groups()
                return f"{prefix}; missing symbol: {symbol} from {module}"
        return f"{prefix}; import target unavailable"

    status_code = _safe_http_code(error)
    api_status = _safe_api_status(error)
    provider_error = _safe_provider_error_identifier(error)
    bad_request_field_paths = _safe_bad_request_field_paths(error)
    if status_code is not None:
        detail = f"Google API HTTP {status_code}"
        if api_status:
            detail += f" ({api_status})"
        else:
            detail += "; provider status unavailable"
        if provider_error and provider_error != api_status:
            detail += f"; provider_error={provider_error}"
        if bad_request_field_paths:
            detail += f"; invalid_fields={','.join(bad_request_field_paths)}"
        return f"{prefix}; {detail}"
    if api_status:
        detail = f"Google API status {api_status}"
        if provider_error and provider_error != api_status:
            detail += f"; provider_error={provider_error}"
        if bad_request_field_paths:
            detail += f"; invalid_fields={','.join(bad_request_field_paths)}"
        return f"{prefix}; {detail}"
    if provider_error:
        return f"{prefix}; provider error {provider_error}"

    return f"{prefix}; provider reason unavailable"


def generate_career_explanation(
    context: CareerExplanationContext,
    *,
    client_factory: Callable[[str], _GeminiClient] | None = None,
) -> GeminiExplanationResult:
    """Generate optional text without influencing deterministic ranking or scores."""
    fallback_text = _build_fallback_explanation(context)
    api_key = _configured_api_key()
    if api_key is None:
        return GeminiExplanationResult(
            GeminiStatus.MISSING_CONFIG,
            fallback_text=fallback_text,
        )

    try:
        client = (client_factory or _create_client)(api_key)
    except Exception as error:
        status = _exception_status(error)
        diagnostic = _safe_diagnostic(error, "client initialization")
        logger.warning(
            "Gemini client initialization failed: category=%s, %s.",
            status.value,
            diagnostic,
        )
        return GeminiExplanationResult(
            status,
            diagnostic=diagnostic,
            fallback_text=fallback_text,
        )

    model = _configured_model()
    prompt = _build_prompt(context)
    for attempt in range(GEMINI_MAX_REQUEST_ATTEMPTS):
        started_at = datetime.now(timezone.utc)
        started_counter = time.perf_counter()
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    "http_options": {"timeout": GEMINI_REQUEST_TIMEOUT_MS},
                    "max_output_tokens": GEMINI_MAX_OUTPUT_TOKENS,
                    "thinking_config": {
                        "thinking_level": GEMINI_THINKING_LEVEL,
                    },
                },
            )
            _log_request_attempt(
                started_at=started_at,
                started_counter=started_counter,
                attempt=attempt + 1,
                model=model,
                api_key=api_key,
                outcome="success",
                category=GeminiStatus.SUCCESS.value,
                http_status=None,
                correlation_id=_provider_correlation_id(response, api_key),
            )
        except Exception as error:
            status = _exception_status(error)
            diagnostic = _safe_diagnostic(
                error,
                "request execution",
                model=model,
                api_key=api_key,
            )
            retrying = (
                attempt + 1 < GEMINI_MAX_REQUEST_ATTEMPTS
                and _is_retryable_request_error(error)
            )
            _log_request_attempt(
                started_at=started_at,
                started_counter=started_counter,
                attempt=attempt + 1,
                model=model,
                api_key=api_key,
                outcome="failure",
                category=status.value,
                http_status=_safe_http_code(error),
                correlation_id=_provider_correlation_id(error, api_key),
                diagnostic=diagnostic,
                retrying=retrying,
            )
            if (
                retrying
            ):
                logger.warning(
                    "Transient Gemini explanation request failure; retrying once: "
                    "attempt=%s, model=%s, category=%s, %s.",
                    attempt + 1,
                    _safe_model_identifier(model, api_key),
                    status.value,
                    diagnostic,
                )
                time.sleep(GEMINI_RETRY_BACKOFF_SECONDS)
                continue
            logger.warning(
                "Gemini explanation request failed: category=%s, %s.",
                status.value,
                diagnostic,
            )
            return GeminiExplanationResult(
                status,
                diagnostic=diagnostic,
                fallback_text=fallback_text,
            )
        break

    try:
        response_text = getattr(response, "text", _MISSING_RESPONSE_TEXT)
    except Exception as error:
        logger.warning(
            "Gemini returned an invalid response format (%s).",
            type(error).__name__,
        )
        return GeminiExplanationResult(
            GeminiStatus.INVALID_RESPONSE,
            fallback_text=fallback_text,
        )
    if response_text is _MISSING_RESPONSE_TEXT:
        return GeminiExplanationResult(
            GeminiStatus.INVALID_RESPONSE,
            fallback_text=fallback_text,
        )
    if response_text is None or response_text == "":
        return GeminiExplanationResult(
            GeminiStatus.EMPTY_RESPONSE,
            fallback_text=fallback_text,
        )
    if not isinstance(response_text, str):
        return GeminiExplanationResult(
            GeminiStatus.INVALID_RESPONSE,
            fallback_text=fallback_text,
        )
    if not response_text.strip():
        return GeminiExplanationResult(
            GeminiStatus.EMPTY_RESPONSE,
            fallback_text=fallback_text,
        )
    return GeminiExplanationResult(GeminiStatus.SUCCESS, response_text.strip())
