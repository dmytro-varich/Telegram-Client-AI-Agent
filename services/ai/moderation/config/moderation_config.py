from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ModerationResult:
    """Result of AI moderation check."""
    should_delete: bool = False
    should_warn: bool = False
    reason: Optional[str] = None
    confidence: float = 0.0
    violations: list[str] = None 