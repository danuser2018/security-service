from typing import Dict, Optional
from app.models.security import ChannelPolicy, RiskLevel

class ChannelPolicyManager:
    def __init__(self):
        # Default policies according to spec:
        # voice -> high, cli -> medium, api -> low
        self._channels: Dict[str, ChannelPolicy] = {
            "voice": ChannelPolicy(max_risk=RiskLevel.HIGH),
            "cli": ChannelPolicy(max_risk=RiskLevel.MEDIUM),
            "api": ChannelPolicy(max_risk=RiskLevel.LOW),
        }

    def get_policy(self, channel_id: str) -> Optional[ChannelPolicy]:
        return self._channels.get(channel_id)

    def update_policy(self, channel_id: str, max_risk: RiskLevel) -> ChannelPolicy:
        policy = ChannelPolicy(max_risk=max_risk)
        self._channels[channel_id] = policy
        return policy

    def get_all_channels(self) -> Dict[str, ChannelPolicy]:
        return self._channels

    def clear(self):
        self._channels.clear()
