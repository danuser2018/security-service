from fastapi import FastAPI
from app.config import settings
from app.api import routes
from app.services.risk_evaluator import RiskEvaluator
from app.services.token_manager import AuthorizationTokenManager
from app.services.authorization_engine import AuthorizationEngine

app = FastAPI(title=settings.SERVICE_NAME)

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
