import pytest
from app.models.security import RiskLevel
from app.services.channel_policy_manager import ChannelPolicyManager

def test_default_channel_policies():
    mgr = ChannelPolicyManager()
    assert mgr.get_policy("voice").max_risk == RiskLevel.HIGH
    assert mgr.get_policy("cli").max_risk == RiskLevel.MEDIUM
    assert mgr.get_policy("hotkey").max_risk == RiskLevel.MEDIUM
    assert mgr.get_policy("api").max_risk == RiskLevel.LOW
    assert mgr.get_policy("unknown") is None

def test_update_channel_policy():
    mgr = ChannelPolicyManager()
    updated = mgr.update_policy("cli", RiskLevel.HIGH)
    assert updated.max_risk == RiskLevel.HIGH
    assert mgr.get_policy("cli").max_risk == RiskLevel.HIGH
