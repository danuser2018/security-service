import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_actions_api():
    payload = {
        "plugin_id": "set-volume",
        "actions": [
            {
                "id": "set-volume",
                "risk": {
                    "policy": "fixed",
                    "value": "low"
                }
            }
        ]
    }
    response = client.post("/v1/security/actions/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["registered_actions"] == 1
