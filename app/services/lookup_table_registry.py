from typing import Dict, Any, Optional, List
from app.models.security import RiskLevel

class LookupTableRegistry:
    def __init__(self):
        # table_name -> { entry_name -> RiskLevel }
        self._tables: Dict[str, Dict[str, RiskLevel]] = {}

    def register_table(self, table_name: str, entries: List[Dict[str, Any]]) -> int:
        if table_name not in self._tables:
            self._tables[table_name] = {}

        count = 0
        for entry in entries:
            name = entry.get("name")
            risk_str = entry.get("risk") or entry.get("risk_level")
            if name and risk_str:
                self._tables[table_name][str(name)] = RiskLevel(risk_str)
                count += 1
        return count

    def get_entry_risk(self, table_name: str, entry_name: str) -> Optional[RiskLevel]:
        table = self._tables.get(table_name)
        if table is None:
            return None
        return table.get(str(entry_name))

    def clear(self):
        self._tables.clear()
