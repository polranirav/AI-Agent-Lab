from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class GuardrailDecision:
    allowed: bool
    action: str
    reason:str
    content: Optional[str] = None
    details: Dict[str, Any] = None