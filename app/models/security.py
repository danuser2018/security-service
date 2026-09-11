from enum import Enum
from typing import Literal, Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    def __le__(self, other: "RiskLevel") -> bool:
        if not isinstance(other, RiskLevel):
            other = RiskLevel(other)
        order = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3}
        return order[self] <= order[other]

    def __lt__(self, other: "RiskLevel") -> bool:
        if not isinstance(other, RiskLevel):
            other = RiskLevel(other)
        order = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3}
        return order[self] < order[other]

    def __ge__(self, other: "RiskLevel") -> bool:
        if not isinstance(other, RiskLevel):
            other = RiskLevel(other)
        order = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3}
        return order[self] >= order[other]

    def __gt__(self, other: "RiskLevel") -> bool:
        if not isinstance(other, RiskLevel):
            other = RiskLevel(other)
        order = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3}
        return order[self] > order[other]


class FixedRiskPolicy(BaseModel):
    policy: Literal["fixed"] = "fixed"
    value: RiskLevel


class LookupRiskPolicy(BaseModel):
    policy: Literal["lookup"] = "lookup"
    source: str
    table: str


RiskPolicy = Union[FixedRiskPolicy, LookupRiskPolicy]


class ActionDefinition(BaseModel):
    id: str
    risk: RiskPolicy


class RegisterActionsRequest(BaseModel):
    plugin_id: str
    actions: List[ActionDefinition]


class ChannelPolicy(BaseModel):
    max_risk: RiskLevel


class ChannelPolicyConfig(BaseModel):
    channels: Dict[str, ChannelPolicy]


class ExecutionPlanActionStep(BaseModel):
    action_id: str
    parameters: Dict[str, Any] = {}


class ExecutionPlanPayload(BaseModel):
    execution_id: str
    actions: List[ExecutionPlanActionStep]


class SecurityContextPayload(BaseModel):
    channel: str


class AuthorizationRequest(BaseModel):
    execution_plan: ExecutionPlanPayload
    security_context: SecurityContextPayload


class AuthorizationTokenItem(BaseModel):
    action_id: str
    token: str


class AuthorizationResponse(BaseModel):
    decision: Literal["ALLOW", "DENY"]
    authorization_tokens: Optional[List[AuthorizationTokenItem]] = None
    reason: Optional[str] = None
