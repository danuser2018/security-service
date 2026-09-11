from typing import Dict, Optional
from app.models.security import ActionDefinition, RegisterActionsRequest

class ActionRegistry:
    def __init__(self):
        self._actions: Dict[str, ActionDefinition] = {}

    def register_actions(self, request: RegisterActionsRequest) -> int:
        count = 0
        for action in request.actions:
            self._actions[action.id] = action
            count += 1
        return count

    def get_action(self, action_id: str) -> Optional[ActionDefinition]:
        return self._actions.get(action_id)

    def clear(self):
        self._actions.clear()
