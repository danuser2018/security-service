import time
import pytest
from app.services.token_manager import AuthorizationTokenManager

def test_token_generation_and_verification():
    tm = AuthorizationTokenManager(secret="my-secret-key", ttl_seconds=60)
    token = tm.generate_token(execution_id="exec-123", action_id="set-volume")

    payload = tm.verify_token(token, expected_execution_id="exec-123", expected_action_id="set-volume")
    assert payload["execution_id"] == "exec-123"
    assert payload["action_id"] == "set-volume"
    assert payload["audience"] == "nova-orchestrator"

def test_token_mismatch_execution_id():
    tm = AuthorizationTokenManager(secret="my-secret-key", ttl_seconds=60)
    token = tm.generate_token(execution_id="exec-123", action_id="set-volume")

    with pytest.raises(ValueError) as exc:
        tm.verify_token(token, expected_execution_id="exec-999", expected_action_id="set-volume")
    assert "execution_id" in str(exc.value)

def test_token_mismatch_action_id():
    tm = AuthorizationTokenManager(secret="my-secret-key", ttl_seconds=60)
    token = tm.generate_token(execution_id="exec-123", action_id="set-volume")

    with pytest.raises(ValueError) as exc:
        tm.verify_token(token, expected_execution_id="exec-123", expected_action_id="other-action")
    assert "action_id" in str(exc.value)

def test_expired_token():
    tm = AuthorizationTokenManager(secret="my-secret-key", ttl_seconds=-10)
    token = tm.generate_token(execution_id="exec-123", action_id="set-volume")

    with pytest.raises(ValueError) as exc:
        tm.verify_token(token, expected_execution_id="exec-123", expected_action_id="set-volume")
    assert "expired" in str(exc.value)

def test_invalid_signature():
    tm1 = AuthorizationTokenManager(secret="secret-1", ttl_seconds=60)
    tm2 = AuthorizationTokenManager(secret="secret-2", ttl_seconds=60)

    token = tm1.generate_token(execution_id="exec-123", action_id="set-volume")
    with pytest.raises(ValueError) as exc:
        tm2.verify_token(token, expected_execution_id="exec-123", expected_action_id="set-volume")
    assert "signature" in str(exc.value).lower() or "invalid" in str(exc.value).lower()
