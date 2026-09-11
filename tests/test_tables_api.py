import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_host_commands_table_api():
    payload = {
        "commands": [
            {"name": "calculator", "risk": "low"},
            {"name": "backup", "risk": "medium"},
            {"name": "format-disk", "risk": "high"}
        ]
    }
    response = client.post("/v1/security/tables/host_commands", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["table"] == "host_commands"
    assert data["entries_registered"] == 3
