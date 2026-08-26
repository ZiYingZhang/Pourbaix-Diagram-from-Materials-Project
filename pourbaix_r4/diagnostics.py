"""Safe, user-actionable summaries for failed R4 calculations."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence

from pourbaix_r4.credentials import CredentialError


_STAGE_LABELS = {
    "credential": "Credential resolution",
    "fetch": "Materials Project query",
    "calculation": "Pourbaix calculation",
}
_KEY_VALUE_PATTERN = re.compile(r"(?i)(api[ _-]?key|token|secret)\s*[:=]\s*[^\s,;]+")


def _status_code(error: Exception) -> int | None:
    for candidate in (error, getattr(error, "response", None)):
        value = getattr(candidate, "status_code", None)
        if isinstance(value, int):
            return value
    return None


def _is_network_error(error: Exception) -> bool:
    if isinstance(error, (ConnectionError, TimeoutError)):
        return True
    name = type(error).__name__.casefold()
    return any(token in name for token in ("connection", "timeout", "network"))


def _category(stage: str, error: Exception) -> str:
    if isinstance(error, CredentialError) or stage == "credential":
        return "credential"
    if _status_code(error) in {401, 403}:
        return "authentication"
    if _is_network_error(error):
        return "network"
    return stage if stage in _STAGE_LABELS else "unknown"


def _redact(message: str, secrets: Iterable[str | None]) -> str:
    safe = str(message)
    for secret in secrets:
        if secret:
            safe = safe.replace(secret, "[redacted]")
    safe = _KEY_VALUE_PATTERN.sub(r"\1=[redacted]", safe)
    return safe[:600] or "No additional error message was provided."


def failure_summary(stage: str, error: Exception, *, secrets: Iterable[str | None] = ()) -> str:
    """Return a short next-step message without echoing credentials."""
    category = _category(stage, error)
    if category == "credential":
        return "API key is required. Open API Settings."
    if category == "authentication":
        return "Materials Project rejected the API key. Verify it in API Settings."
    if category == "network":
        return "Could not reach Materials Project. Check the internet connection and try again."
    if category == "fetch":
        return "Materials Project query failed. Open Diagnostics for details."
    if category == "calculation":
        return "Pourbaix calculation failed. Open Diagnostics for details."
    return "Calculation failed. Open Diagnostics for details."


def diagnostics_text(
    stage: str,
    error: Exception,
    *,
    secrets: Iterable[str | None] = (),
    extra_lines: Sequence[str] = (),
) -> str:
    """Return a copy-safe technical summary for the in-app Diagnostics dialog."""
    category = _category(stage, error)
    lines = [
        "Calculation diagnostics",
        f"Stage: {_STAGE_LABELS.get(stage, 'Unknown')}",
        f"Category: {category.title()}",
        f"Exception: {type(error).__name__}",
        f"Details: {_redact(str(error), secrets)}",
        *extra_lines,
        "API keys are never shown in diagnostics.",
    ]
    return "\n".join(lines)
