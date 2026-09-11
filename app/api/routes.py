from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Body, Path
from pydantic import BaseModel

from app.models.security import (
    RegisterActionsRequest,
    AuthorizationRequest,
    AuthorizationResponse,
    ChannelPolicy,
    RiskLevel
)
from app.services.action_registry import ActionRegistry
from app.services.lookup_table_registry import LookupTableRegistry
from app.services.channel_policy_manager import ChannelPolicyManager
from app.services.authorization_engine import AuthorizationEngine

router = APIRouter()

# Singletons / Dependency instances initialized by main
action_registry = ActionRegistry()
lookup_table_registry = LookupTableRegistry()
channel_policy_manager = ChannelPolicyManager()
authorization_engine: Optional[AuthorizationEngine] = None

class TableRegistrationPayload(BaseModel):
    commands: Optional[List[Dict[str, Any]]] = None
    entries: Optional[List[Dict[str, Any]]] = None

class ChannelPolicyUpdatePayload(BaseModel):
    max_risk: RiskLevel

@router.post("/v1/security/actions/register")
def register_actions(request: RegisterActionsRequest):
    count = action_registry.register_actions(request)
    return {"success": True, "registered_actions": count}

@router.post("/v1/security/tables/{table_name}")
def register_table(
    table_name: str = Path(...),
    payload: TableRegistrationPayload = Body(...)
):
    entries = payload.commands if payload.commands is not None else payload.entries
    if entries is None:
        entries = []
    count = lookup_table_registry.register_table(table_name, entries)
    return {
        "success": True,
        "table": table_name,
        "entries_registered": count
    }

@router.post("/v1/security/authorize", response_model=AuthorizationResponse)
def authorize_execution_plan(request: AuthorizationRequest):
    if authorization_engine is None:
        raise HTTPException(status_code=500, detail="Authorization engine not initialized")
    return authorization_engine.authorize(request)

@router.get("/v1/security/channels")
def get_channel_policies():
    channels = channel_policy_manager.get_all_channels()
    return {"channels": {k: {"max_risk": v.max_risk.value} for k, v in channels.items()}}

@router.put("/v1/security/channels/{channel_id}")
def update_channel_policy(channel_id: str, payload: ChannelPolicyUpdatePayload):
    updated = channel_policy_manager.update_policy(channel_id, payload.max_risk)
    return {
        "success": True,
        "channel": channel_id,
        "max_risk": updated.max_risk.value
    }

@router.get("/health")
def health_check():
    return {"status": "ok"}
