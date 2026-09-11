from typing import Dict, Any
from app.models.security import ActionDefinition, FixedRiskPolicy, LookupRiskPolicy, RiskLevel
from app.services.lookup_table_registry import LookupTableRegistry

class RiskEvaluationError(Exception):
    def __init__(self, reason: str, error_code: str):
        super().__init__(reason)
        self.reason = reason
        self.error_code = error_code

class RiskEvaluator:
    def __init__(self, table_registry: LookupTableRegistry):
        self._table_registry = table_registry

    def evaluate(self, action_def: ActionDefinition, parameters: Dict[str, Any]) -> RiskLevel:
        policy = action_def.risk
        policy_type = getattr(policy, "policy", None)

        if isinstance(policy, FixedRiskPolicy) or policy_type == "fixed":
            return policy.value
        elif isinstance(policy, LookupRiskPolicy) or policy_type == "lookup":
            source_param = policy.source
            table_name = policy.table

            if source_param not in parameters:
                raise RiskEvaluationError(
                    reason=f"Missing required parameter '{source_param}' for lookup policy on action '{action_def.id}'",
                    error_code="MISSING_SOURCE_PARAMETER"
                )

            param_value = parameters[source_param]
            risk_level = self._table_registry.get_entry_risk(table_name, param_value)

            if risk_level is None:
                if table_name not in self._table_registry._tables:
                    raise RiskEvaluationError(
                        reason=f"Lookup table '{table_name}' not found for action '{action_def.id}'",
                        error_code="LOOKUP_TABLE_NOT_FOUND"
                    )
                else:
                    raise RiskEvaluationError(
                        reason=f"Value '{param_value}' not found in lookup table '{table_name}' for action '{action_def.id}'",
                        error_code="LOOKUP_VALUE_NOT_FOUND"
                    )
            return risk_level
        else:
            raise RiskEvaluationError(
                reason=f"Invalid risk policy type for action '{action_def.id}'",
                error_code="INVALID_RISK_POLICY"
            )
