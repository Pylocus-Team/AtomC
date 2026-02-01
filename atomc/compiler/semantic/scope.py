"""
Rynx 2.0 Scope — Stack-based scope. One scope per block.
No magic. Explicit push/pop. Block-scoped variables.
"""

from typing import Dict, Optional

from atomc.ast.ast_nodes import TypeKind


class Scope:
    """Single scope: map from name to (type_kind, is_let)."""

    def __init__(self, parent: Optional["Scope"] = None) -> None:
        self.parent = parent
        self.symbols: Dict[str, tuple[TypeKind, bool]] = {}

    def declare(self, name: str, type_kind: TypeKind, is_let: bool = False) -> None:
        self.symbols[name] = (type_kind, is_let)

    def get(self, name: str) -> Optional[tuple[TypeKind, bool]]:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.get(name)
        return None

    def get_local(self, name: str) -> Optional[tuple[TypeKind, bool]]:
        return self.symbols.get(name)

    def has_local(self, name: str) -> bool:
        return name in self.symbols


class ScopeStack:
    """Stack of scopes. Push on block enter, pop on block exit."""

    def __init__(self) -> None:
        self.stack: list[Scope] = [Scope()]

    def push(self) -> None:
        self.stack.append(Scope(parent=self.stack[-1]))

    def pop(self) -> None:
        if len(self.stack) > 1:
            self.stack.pop()

    def current(self) -> Scope:
        return self.stack[-1]

    def declare(self, name: str, type_kind: TypeKind, is_let: bool = False) -> None:
        self.current().declare(name, type_kind, is_let)

    def get(self, name: str) -> Optional[tuple[TypeKind, bool]]:
        return self.current().get(name)

    def has_local(self, name: str) -> bool:
        return self.current().has_local(name)
