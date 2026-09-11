import pytest
from app.models.security import RiskLevel

def test_risk_level_ordering():
    assert RiskLevel.LOW < RiskLevel.MEDIUM
    assert RiskLevel.MEDIUM < RiskLevel.HIGH
    assert RiskLevel.LOW < RiskLevel.HIGH

    assert RiskLevel.LOW <= RiskLevel.LOW
    assert RiskLevel.LOW <= RiskLevel.MEDIUM
    assert RiskLevel.MEDIUM <= RiskLevel.HIGH

    assert RiskLevel.HIGH > RiskLevel.MEDIUM
    assert RiskLevel.MEDIUM > RiskLevel.LOW

    assert RiskLevel.HIGH >= RiskLevel.HIGH
    assert RiskLevel.HIGH >= RiskLevel.MEDIUM

def test_risk_level_comparison_with_strings():
    assert RiskLevel.LOW < "medium"
    assert RiskLevel.MEDIUM <= "high"
    assert RiskLevel.HIGH > "medium"
