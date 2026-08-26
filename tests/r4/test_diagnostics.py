from pourbaix_r4.credentials import CredentialError
from pourbaix_r4.diagnostics import diagnostics_text, failure_summary


def test_credential_failure_summary_is_actionable_and_does_not_expose_key():
    key = "test-secret-api-key"
    error = CredentialError(f"A Materials Project API key is required: {key}")

    summary = failure_summary("credential", error, secrets=(key,))
    details = diagnostics_text("credential", error, secrets=(key,))

    assert summary == "API key is required. Open API Settings."
    assert "Credential" in details
    assert key not in details


def test_network_and_auth_failures_are_distinguished_safely():
    class AuthenticationFailure(RuntimeError):
        status_code = 401

    assert failure_summary("fetch", AuthenticationFailure("bad key")) == (
        "Materials Project rejected the API key. Verify it in API Settings."
    )
    assert failure_summary("fetch", ConnectionError("offline")) == (
        "Could not reach Materials Project. Check the internet connection and try again."
    )
