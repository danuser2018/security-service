import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from nova_event_bus import NatsEventBus, EventBusConfig
from app.config import settings
from app.api import routes
from app.models.events import HostCommandsAvailableEvent
from app.services.risk_evaluator import RiskEvaluator
from app.services.token_manager import AuthorizationTokenManager
from app.services.authorization_engine import AuthorizationEngine

logger = logging.getLogger(__name__)


def sync_host_commands(commands: list) -> int:
    entries = [
        {
            "name": c["name"] if isinstance(c, dict) else getattr(c, "name", None),
            "risk": c["risk"] if isinstance(c, dict) else getattr(c, "risk", None),
        }
        for c in (commands or [])
    ]
    return routes.lookup_table_registry.register_table("host_commands", entries)


@asynccontextmanager
async def lifespan(app: FastAPI):
    event_bus = NatsEventBus(config=EventBusConfig(nats_url=settings.NATS_URL))
    try:
        await event_bus.connect()
        logger.info(f"Connected to NATS event bus at {settings.NATS_URL}")

        async def handle_commands_available(evt: HostCommandsAvailableEvent):
            commands = getattr(evt, "commands", []) or []
            logger.info(f"Received {len(commands)} commands from host-service via NATS")
            count = sync_host_commands(commands)
            logger.info(f"Registered {count} entries in lookup table 'host_commands'")

        await event_bus.subscribe(HostCommandsAvailableEvent, handle_commands_available)
        logger.info("Subscribed to HostCommandsAvailableEvent on event.host.commands.available")
    except Exception as exc:
        logger.warning(f"Failed to connect or subscribe to NATS on startup: {exc}")

    app.state.event_bus = event_bus

    yield

    try:
        await event_bus.disconnect()
        logger.info("Disconnected from NATS event bus")
    except Exception as exc:
        logger.warning(f"Error disconnecting from NATS: {exc}")


app = FastAPI(title=settings.SERVICE_NAME, version="1.2.1", lifespan=lifespan)

# Initialize Authorization Engine
risk_evaluator = RiskEvaluator(routes.lookup_table_registry)
token_manager = AuthorizationTokenManager(
    secret=settings.SECURITY_HMAC_SECRET,
    ttl_seconds=settings.TOKEN_TTL_SECONDS
)
routes.authorization_engine = AuthorizationEngine(
    action_registry=routes.action_registry,
    table_registry=routes.lookup_table_registry,
    channel_policy_manager=routes.channel_policy_manager,
    risk_evaluator=risk_evaluator,
    token_manager=token_manager
)

app.include_router(routes.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
