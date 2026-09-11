import pytest
from app.models.security import (
    ActionDefinition,
    FixedRiskPolicy,
    LookupRiskPolicy,
    RiskLevel,
    AuthorizationRequest,
    ExecutionPlanPayload,
    ExecutionPlanActionStep,
    SecurityContextPayload,
    RegisterActionsRequest
)
from app.services.action_registry import ActionRegistry
from app.services.lookup_table_registry import LookupTableRegistry
from app.services.channel_policy_manager import ChannelPolicyManager
from app.services.risk_evaluator import RiskEvaluator
from app.services.token_manager import AuthorizationTokenManager
from app.services.authorization_engine import AuthorizationEngine

def create_engine():
    action_reg = ActionRegistry()
    table_reg = LookupTableRegistry()
    channel_mgr = ChannelPolicyManager()
    evaluator = RiskEvaluator(table_reg)
    token_mgr = AuthorizationTokenManager(secret="test-secret", ttl_seconds=300)

    # Register fixed action
    action_reg.register_actions(RegisterActionsRequest(
        plugin_id="set-volume",
        actions=[ActionDefinition(id="set-volume", risk=FixedRiskPolicy(value=RiskLevel.LOW))]
    ))
    # Register lookup action
    action_reg.register_actions(RegisterActionsRequest(
        plugin_id="host-service",
        actions=[ActionDefinition(id="execute-command", risk=LookupRiskPolicy(source="command", table="host_commands"))]
    ))
    # Register host table
    table_reg.register_table("host_commands", [
        {"name": "backup", "risk": "medium"},
        {"name": "format-disk", "risk": "high"}
    ])

    engine = AuthorizationEngine(action_reg, table_reg, channel_mgr, evaluator, token_mgr)
    return engine

def test_authorize_low_risk_action_voice_channel_allow():
    engine = create_engine()
    req = AuthorizationRequest(
        execution_plan=ExecutionPlanPayload(
            execution_id="exec-001",
            actions=[ExecutionPlanActionStep(action_id="set-volume", parameters={"volume": 50})]
        ),
        security_context=SecurityContextPayload(channel="voice")
    )
    resp = engine.authorize(req)
    assert resp.decision == "ALLOW"
    assert resp.authorization_tokens is not None
    assert len(resp.authorization_tokens) == 1
    assert resp.authorization_tokens[0].action_id == "set-volume"

def test_authorize_lookup_action_cli_channel_allow():
    engine = create_engine()
    req = AuthorizationRequest(
        execution_plan=ExecutionPlanPayload(
            execution_id="exec-002",
            actions=[ExecutionPlanActionStep(action_id="execute-command", parameters={"command": "backup"})]
        ),
        security_context=SecurityContextPayload(channel="cli")
    )
    resp = engine.authorize(req)
    assert resp.decision == "ALLOW"
    assert len(resp.authorization_tokens) == 1

def test_authorize_risk_exceeds_channel_max_risk_deny():
    engine = create_engine()
    req = AuthorizationRequest(
        execution_plan=ExecutionPlanPayload(
            execution_id="exec-003",
            actions=[ExecutionPlanActionStep(action_id="execute-command", parameters={"command": "format-disk"})]
        ),
        security_context=SecurityContextPayload(channel="cli")
    )
    resp = engine.authorize(req)
    assert resp.decision == "DENY"
    assert resp.authorization_tokens is None
    assert "exceeds channel" in resp.reason

def test_authorize_atomic_plan_fail_closed_deny():
    engine = create_engine()
    req = AuthorizationRequest(
        execution_plan=ExecutionPlanPayload(
            execution_id="exec-004",
            actions=[
                ExecutionPlanActionStep(action_id="set-volume", parameters={"volume": 50}),
                ExecutionPlanActionStep(action_id="execute-command", parameters={"command": "format-disk"})
            ]
        ),
        security_context=SecurityContextPayload(channel="cli")
    )
    resp = engine.authorize(req)
    assert resp.decision == "DENY"
    assert resp.authorization_tokens is None

def test_authorize_unregistered_action_deny():
    engine = create_engine()
    req = AuthorizationRequest(
        execution_plan=ExecutionPlanPayload(
            execution_id="exec-005",
            actions=[ExecutionPlanActionStep(action_id="unknown-action", parameters={})]
        ),
        security_context=SecurityContextPayload(channel="voice")
    )
    resp = engine.authorize(req)
    assert resp.decision == "DENY"
    assert "Unregistered action" in resp.reason

def test_authorize_unregistered_channel_deny():
    engine = create_engine()
    req = AuthorizationRequest(
        execution_plan=ExecutionPlanPayload(
            execution_id="exec-006",
            actions=[ExecutionPlanActionStep(action_id="set-volume", parameters={})]
        ),
        security_context=SecurityContextPayload(channel="unregistered_channel")
    )
    resp = engine.authorize(req)
    assert resp.decision == "DENY"
    assert "Unregistered channel" in resp.reason
