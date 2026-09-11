import pytest
from app.models.security import ActionDefinition, FixedRiskPolicy, RiskLevel
from app.services.lookup_table_registry import LookupTableRegistry
from app.services.risk_evaluator import RiskEvaluator

def test_fixed_risk_policy_evaluation():
    table_registry = LookupTableRegistry()
    evaluator = RiskEvaluator(table_registry)

    action_def = ActionDefinition(
        id="set-volume",
        risk=FixedRiskPolicy(value=RiskLevel.LOW)
    )

    risk = evaluator.evaluate(action_def, parameters={"volume": 50})
    assert risk == RiskLevel.LOW
