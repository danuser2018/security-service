from typing import Optional
from app.models.security import AuthorizationRequest, AuthorizationResponse, AuthorizationTokenItem
from app.services.action_registry import ActionRegistry
from app.services.lookup_table_registry import LookupTableRegistry
from app.services.channel_policy_manager import ChannelPolicyManager
from app.services.risk_evaluator import RiskEvaluator, RiskEvaluationError
from app.services.token_manager import AuthorizationTokenManager

class AuthorizationEngine:
    def __init__(
        self,
        action_registry: ActionRegistry,
        table_registry: LookupTableRegistry,
        channel_policy_manager: ChannelPolicyManager,
        risk_evaluator: RiskEvaluator,
        token_manager: AuthorizationTokenManager
    ):
        self.action_registry = action_registry
        self.table_registry = table_registry
        self.channel_policy_manager = channel_policy_manager
        self.risk_evaluator = risk_evaluator
        self.token_manager = token_manager

    def authorize(self, request: AuthorizationRequest) -> AuthorizationResponse:
        channel_id = request.security_context.channel
        channel_policy = self.channel_policy_manager.get_policy(channel_id)

        if not channel_policy:
            return AuthorizationResponse(
                decision="DENY",
                authorization_tokens=None,
                reason=f"Unregistered channel '{channel_id}'"
            )

        tokens = []
        for step in request.execution_plan.actions:
            action_def = self.action_registry.get_action(step.action_id)
            if not action_def:
                return AuthorizationResponse(
                    decision="DENY",
                    authorization_tokens=None,
                    reason=f"Unregistered action '{step.action_id}'"
                )

            try:
                effective_risk = self.risk_evaluator.evaluate(action_def, step.parameters)
            except RiskEvaluationError as e:
                return AuthorizationResponse(
                    decision="DENY",
                    authorization_tokens=None,
                    reason=e.reason
                )

            if effective_risk > channel_policy.max_risk:
                return AuthorizationResponse(
                    decision="DENY",
                    authorization_tokens=None,
                    reason=f"Action '{step.action_id}' effective risk '{effective_risk.value}' exceeds channel '{channel_id}' max risk '{channel_policy.max_risk.value}'"
                )

            token_str = self.token_manager.generate_token(
                execution_id=request.execution_plan.execution_id,
                action_id=step.action_id
            )
            tokens.append(AuthorizationTokenItem(action_id=step.action_id, token=token_str))

        return AuthorizationResponse(
            decision="ALLOW",
            authorization_tokens=tokens,
            reason=None
        )
