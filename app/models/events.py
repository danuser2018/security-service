from dataclasses import dataclass
from typing import List
from nova_event_bus import Event, event


@dataclass
class PublicCommandEntry:
    name: str
    risk: str
    phrases: List[str]


@event("event.host.commands.available")
@dataclass
class HostCommandsAvailableEvent(Event):
    version: int
    commands: List[PublicCommandEntry]
