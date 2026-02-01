"""
Rynx 2.0 Symbol Table — Tasks and their signatures.
No magic. Explicit register/lookup.
"""

from typing import Dict, List, Optional

from atomc.ast.ast_nodes import ParamNode, TypeKind


class TaskSignature:
    """Task name, parameter types, return type (set after body is analyzed)."""

    def __init__(self, name: str, params: List[ParamNode], returns_value: bool = True) -> None:
        self.name = name
        self.params = params
        self.returns_value = returns_value
        self.return_type: Optional[TypeKind] = None


class SymbolTable:
    """Global map: task name -> TaskSignature."""

    def __init__(self) -> None:
        self.tasks: Dict[str, TaskSignature] = {}

    def register_task(self, name: str, params: List[ParamNode], returns_value: bool = True) -> None:
        if name in self.tasks:
            raise ValueError(f"Task already defined: {name}")
        self.tasks[name] = TaskSignature(name=name, params=params, returns_value=returns_value)

    def get_task(self, name: str) -> Optional[TaskSignature]:
        return self.tasks.get(name)

    def has_task(self, name: str) -> bool:
        return name in self.tasks
