import pytest
from app.api import routes
from app.models.events import HostCommandsAvailableEvent, PublicCommandEntry
from app.models.security import (
    AuthorizationRequest,
    ExecutionPlanPayload,
    ExecutionPlanActionStep,
    SecurityContextPayload,
    RiskLevel,
    RegisterActionsRequest,
    ActionDefinition,
    LookupRiskPolicy,
)
from app.services.lookup_table_registry import LookupTableRegistry
from app.services.risk_evaluator import RiskEvaluator
from app.services.token_manager import AuthorizationTokenManager
from app.services.channel_policy_manager import ChannelPolicyManager
from app.services.action_registry import ActionRegistry
from app.services.authorization_engine import AuthorizationEngine


from app.main import sync_host_commands


@pytest.fixture(autouse=True)
def clean_table_registry():
    routes.lookup_table_registry.clear()
    yield
    routes.lookup_table_registry.clear()


@pytest.mark.asyncio
async def test_nats_catalog_sync_updates_lookup_table():
    evt = HostCommandsAvailableEvent(
        version=1,
        commands=[
            PublicCommandEntry(name="calculator", risk="low", phrases=["calculadora"]),
            PublicCommandEntry(name="backup", risk="medium", phrases=["copia de seguridad"]),
            PublicCommandEntry(name="format-disk", risk="high", phrases=["formatear disco"]),
        ],
    )

    count = sync_host_commands(evt.commands)
    assert count == 3

    assert routes.lookup_table_registry.get_entry_risk("host_commands", "calculator") == RiskLevel.LOW
    assert routes.lookup_table_registry.get_entry_risk("host_commands", "backup") == RiskLevel.MEDIUM
    assert routes.lookup_table_registry.get_entry_risk("host_commands", "format-disk") == RiskLevel.HIGH
    assert routes.lookup_table_registry.get_entry_risk("host_commands", "unknown-cmd") is None


@pytest.mark.asyncio
async def test_nats_catalog_sync_updates_lookup_table_from_dicts():
    # When deserialized over NATS, commands are received as raw dicts
    dict_commands = [
        {"name": "calculator", "risk": "low", "phrases": ["calculadora"]},
        {"name": "backup", "risk": "medium", "phrases": ["copia de seguridad"]},
        {"name": "editor", "risk": "low", "phrases": ["editor"]},
    ]

    count = sync_host_commands(dict_commands)
    assert count == 3

    assert routes.lookup_table_registry.get_entry_risk("host_commands", "calculator") == RiskLevel.LOW
    assert routes.lookup_table_registry.get_entry_risk("host_commands", "backup") == RiskLevel.MEDIUM
    assert routes.lookup_table_registry.get_entry_risk("host_commands", "editor") == RiskLevel.LOW
    assert routes.lookup_table_registry.get_entry_risk("host_commands", "unknown-cmd") is None


@pytest.mark.asyncio
async def test_fail_closed_authorization_unknown_command():
    action_reg = ActionRegistry()
    table_reg = LookupTableRegistry()
    risk_eval = RiskEvaluator(table_reg)
    policy_mgr = ChannelPolicyManager()
    token_mgr = AuthorizationTokenManager(secret="test-secret", ttl_seconds=60)

    engine = AuthorizationEngine(
        action_registry=action_reg,
        table_registry=table_reg,
        channel_policy_manager=policy_mgr,
        risk_evaluator=risk_eval,
        token_manager=token_mgr,
    )

    action_reg.register_actions(
        RegisterActionsRequest(
            plugin_id="commands",
            actions=[
                ActionDefinition(
                    id="commands.execute",
                    risk=LookupRiskPolicy(
                        policy="lookup",
                        source="command",
                        table="host_commands",
                    ),
                )
            ],
        )
    )

    # Scenario 1: Table is empty (catalog not received yet) -> DENY
    req = AuthorizationRequest(
        execution_plan=ExecutionPlanPayload(
            execution_id="exec-1",
            actions=[
                ExecutionPlanActionStep(
                    action_id="commands.execute",
                    parameters={"command": "calculator"},
                )
            ],
        ),
        security_context=SecurityContextPayload(channel="voice"),
    )
    decision = engine.authorize(req)
    assert decision.decision == "DENY"
    assert decision.authorization_tokens is None

    # Scenario 2: Catalog received with calculator, but user requests unregistered-tool -> DENY
    table_reg.register_table("host_commands", [{"name": "calculator", "risk": "low"}])
    req_unknown = AuthorizationRequest(
        execution_plan=ExecutionPlanPayload(
            execution_id="exec-2",
            actions=[
                ExecutionPlanActionStep(
                    action_id="commands.execute",
                    parameters={"command": "unregistered-tool"},
                )
            ],
        ),
        security_context=SecurityContextPayload(channel="voice"),
    )
    decision_unknown = engine.authorize(req_unknown)
    assert decision_unknown.decision == "DENY"
    assert decision_unknown.authorization_tokens is None

    # Scenario 3: Registered command calculator (low risk, voice channel max_risk is high) -> ALLOW
    decision_valid = engine.authorize(req)
    assert decision_valid.decision == "ALLOW"
    assert decision_valid.authorization_tokens is not None
    assert len(decision_valid.authorization_tokens) == 1
    assert decision_valid.authorization_tokens[0].action_id == "commands.execute"
