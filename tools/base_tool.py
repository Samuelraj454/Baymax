from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class ToolResult:
    success: bool
    output: Any
    error: str = ""

class BaseTool(ABC):
    name: str
    description: str
    schema: dict

    def validate_args(self, args: dict) -> tuple[bool, str]:
        return True, ""

    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        pass
