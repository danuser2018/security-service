import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_authorize_endpoint_allow_and_deny():
    # 1. Register action
    action_payload = {
        "plugin_id": "set-volume",
        "actions": [
            {
                "id": "set-volume",
                "risk": {"policy": "fixed", "value": "low"}
            }
        ]
    }
    client.post("/v1/security/actions/register", json=action_payload)

    # 2. Authorize via voice channel -> ALLOW
    auth_payload = {
        "execution_plan": {
            "execution_id": "a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6",
            "actions": [
                {"action_id": "set-volume", "parameters": {"volume": 50}}
            ]
        },
        "security_context": {
            "channel": "voice"
        }
    }
    res = client.post("/v1/security/authorize", json=auth_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "ALLOW"
    assert data["authorization_tokens"] is not None
    assert len(data["authorization_tokens"]) == 1
    assert data["authorization_tokens"][0]["action_id"] == "set-volume"

def test_channels_api_get_and_put():
    # GET channels
    res_get = client.get("/v1/security/channels")
    assert res_get.status_code == 200
    channels = res_get.json()["channels"]
    assert "voice" in channels
    assert channels["cli"]["max_risk"] == "medium"

    # PUT channel
    res_put = client.put("/v1/security/channels/cli", json={"max_risk": "high"})
    assert res_put.status_code == 200
    assert res_put.json()["max_risk"] == "high"

def test_health_api():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
