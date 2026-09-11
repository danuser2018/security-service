import pytest
from app.api import routes
from app.services.action_registry import ActionRegistry
from app.services.lookup_table_registry import LookupTableRegistry
from app.services.channel_policy_manager import ChannelPolicyManager
from app.services.risk_evaluator import RiskEvaluator
from app.services.token_manager import AuthorizationTokenManager
from app.services.authorization_engine import AuthorizationEngine

@pytest.fixture(autouse=True)
def reset_registries():
    routes.action_registry.clear()
    routes.lookup_table_registry.clear()
    routes.channel_policy_manager.clear()
    # Re-initialize default channel policies
    default_mgr = ChannelPolicyManager()
    routes.channel_policy_manager._channels = default_mgr._channels.copy()

    risk_evaluator = RiskEvaluator(routes.lookup_table_registry)
    token_manager = AuthorizationTokenManager(secret="test-secret-key", ttl_seconds=300)
    routes.authorization_engine = AuthorizationEngine(
        action_registry=routes.action_registry,
        table_registry=routes.lookup_table_registry,
        channel_policy_manager=routes.channel_policy_manager,
        risk_evaluator=risk_evaluator,
        token_manager=token_manager
    )
