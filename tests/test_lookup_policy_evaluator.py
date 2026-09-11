import pytest
from app.models.security import ActionDefinition, LookupRiskPolicy, RiskLevel
from app.services.lookup_table_registry import LookupTableRegistry
from app.services.risk_evaluator import RiskEvaluator, RiskEvaluationError

def test_lookup_risk_policy_success():
    table_registry = LookupTableRegistry()
    table_registry.register_table("host_commands", [
        {"name": "calculator", "risk": "low"},
        {"name": "backup", "risk": "medium"},
        {"name": "format-disk", "risk": "high"}
    ])

    evaluator = RiskEvaluator(table_registry)
    action_def = ActionDefinition(
        id="execute-command",
        risk=LookupRiskPolicy(source="command", table="host_commands")
    )

    risk = evaluator.evaluate(action_def, parameters={"command": "backup"})
    assert risk == RiskLevel.MEDIUM

def test_lookup_missing_parameter():
    table_registry = LookupTableRegistry()
    table_registry.register_table("host_commands", [{"name": "backup", "risk": "medium"}])
    evaluator = RiskEvaluator(table_registry)

    action_def = ActionDefinition(
        id="execute-command",
        risk=LookupRiskPolicy(source="command", table="host_commands")
    )

    with pytest.raises(RiskEvaluationError) as exc_info:
        evaluator.evaluate(action_def, parameters={})
    assert exc_info.value.error_code == "MISSING_SOURCE_PARAMETER"

def test_lookup_table_not_found():
    table_registry = LookupTableRegistry()
    evaluator = RiskEvaluator(table_registry)

    action_def = ActionDefinition(
        id="execute-command",
        risk=LookupRiskPolicy(source="command", table="non_existent_table")
    )

    with pytest.raises(RiskEvaluationError) as exc_info:
        evaluator.evaluate(action_def, parameters={"command": "backup"})
    assert exc_info.value.error_code == "LOOKUP_TABLE_NOT_FOUND"

def test_lookup_value_not_found():
    table_registry = LookupTableRegistry()
    table_registry.register_table("host_commands", [{"name": "backup", "risk": "medium"}])
    evaluator = RiskEvaluator(table_registry)

    action_def = ActionDefinition(
        id="execute-command",
        risk=LookupRiskPolicy(source="command", table="host_commands")
    )

    with pytest.raises(RiskEvaluationError) as exc_info:
        evaluator.evaluate(action_def, parameters={"command": "unknown_cmd"})
    assert exc_info.value.error_code == "LOOKUP_VALUE_NOT_FOUND"
