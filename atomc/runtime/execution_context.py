"""
Rynx 2.0 Execution Context — Stack-based scope, task registry.
Runtime only. No type checks. No semantics.
"""

from typing import Dict, Any, List, Optional

from atomc.ast.ast_nodes import ProgramNode, TaskDeclNode


class ExecutionContext:
    """Runtime scope stack and task map."""

    def __init__(self, program: ProgramNode) -> None:
        self.program = program
        self.scopes: List[Dict[str, Any]] = [{}]
        self.tasks: Dict[str, TaskDeclNode] = {}
        for task in program.tasks:
            self.tasks[task.name] = task

    def push_scope(self) -> None:
        self.scopes.append({})

    def pop_scope(self) -> None:
        if len(self.scopes) > 1:
            self.scopes.pop()

    def current_scope(self) -> Dict[str, Any]:
        return self.scopes[-1]

    def get(self, name: str) -> Any:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise KeyError(name)

    def set(self, name: str, value: Any) -> None:
        self.current_scope()[name] = value

    def declare(self, name: str, value: Any) -> None:
        self.current_scope()[name] = value

    def get_task(self, name: str) -> Optional[TaskDeclNode]:
        return self.tasks.get(name)
