"""
Rynx 2.0 AST Nodes — Explicit structures per specification.
One concept = one structure. No magic helpers. No dynamic behavior.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Union, Tuple


# Optional source location for diagnostics (line, column) 1-based
Loc = Tuple[int, int]


# ---------------------------------------------------------------------------
# Type and variant enums (canonical)
# ---------------------------------------------------------------------------

class TypeKind(Enum):
    NUM = "num"
    DEC = "dec"
    TEXT = "text"
    YES = "yes"
    NUMS = "nums"
    TEXTS = "texts"
    DECS = "decs"
    YESS = "yess"
    GUESS = "guess"
    VOID = "void"


class BinaryOp(Enum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="
    EQ = "=="
    NE = "!="
    AND = "&&"
    OR = "||"


class UnaryOp(Enum):
    NOT = "!"
    NEG = "-"


class LoopVariantKind(Enum):
    RANGE = "range"
    LIST = "list"
    INFINITE = "infinite"


# ---------------------------------------------------------------------------
# Expression nodes (primary hierarchy)
# ---------------------------------------------------------------------------

class Expr(ABC):
    """Base for all expressions. No implicit behavior."""

    @abstractmethod
    def __repr__(self) -> str:
        pass


@dataclass
class NumLiteral(Expr):
    value: Union[int, float]
    loc: Loc = (0, 0)

    def __repr__(self) -> str:
        return f"NumLiteral({self.value})"


@dataclass
class TextLiteral(Expr):
    value: str
    loc: Loc = (0, 0)

    def __repr__(self) -> str:
        return f"TextLiteral({repr(self.value)})"


@dataclass
class BoolLiteral(Expr):
    value: bool

    def __repr__(self) -> str:
        return f"BoolLiteral({self.value})"


@dataclass
class VariableExpr(Expr):
    name: str
    loc: Loc = (0, 0)

    def __repr__(self) -> str:
        return f"VariableExpr({self.name})"


@dataclass
class BinaryExpr(Expr):
    left: Expr
    op: BinaryOp
    right: Expr
    loc: Loc = (0, 0)

    def __repr__(self) -> str:
        return f"BinaryExpr({self.left!r}, {self.op.value}, {self.right!r})"


@dataclass
class UnaryExpr(Expr):
    op: UnaryOp
    expr: Expr

    def __repr__(self) -> str:
        return f"UnaryExpr({self.op.value}, {self.expr!r})"


@dataclass
class CallExpr(Expr):
    name: str
    args: List[Expr]
    loc: Loc = (0, 0)

    def __repr__(self) -> str:
        return f"CallExpr({self.name}, {self.args!r})"


@dataclass
class IndexExpr(Expr):
    target: Expr
    index: Expr

    def __repr__(self) -> str:
        return f"IndexExpr({self.target!r}, {self.index!r})"


@dataclass
class RangeExpr(Expr):
    start: Expr
    end: Expr
    step: Optional[Expr] = None

    def __repr__(self) -> str:
        return f"RangeExpr({self.start!r}, {self.end!r}, step={self.step!r})"


@dataclass
class BlockExpr(Expr):
    body: "BlockNode"

    def __repr__(self) -> str:
        return f"BlockExpr({self.body!r})"


# ---------------------------------------------------------------------------
# Statement and block
# ---------------------------------------------------------------------------

class Stmt(ABC):
    """Base for all statements."""

    @abstractmethod
    def __repr__(self) -> str:
        pass


@dataclass
class BlockNode:
    statements: List[Stmt]

    def __repr__(self) -> str:
        return f"BlockNode({len(self.statements)} stmts)"


# ---------------------------------------------------------------------------
# Param for tasks
# ---------------------------------------------------------------------------

@dataclass
class ParamNode:
    type_kind: TypeKind
    name: str

    def __repr__(self) -> str:
        return f"Param({self.type_kind.value}, {self.name})"


# ---------------------------------------------------------------------------
# Loop variant (range / list / infinite)
# ---------------------------------------------------------------------------

@dataclass
class LoopVariant:
    kind: LoopVariantKind
    name: Optional[str] = None
    range_expr: Optional[RangeExpr] = None
    list_expr: Optional[Expr] = None

    def __repr__(self) -> str:
        return f"LoopVariant({self.kind}, name={self.name}, range={self.range_expr}, list={self.list_expr})"


# ---------------------------------------------------------------------------
# Statement nodes
# ---------------------------------------------------------------------------

@dataclass
class VariableDeclNode(Stmt):
    type_kind: TypeKind
    name: str
    value: Expr
    loc: Loc = (0, 0)

    def __repr__(self) -> str:
        return f"VariableDeclNode({self.type_kind.value}, {self.name})"


@dataclass
class GuessDeclNode(Stmt):
    name: str
    value: Expr
    loc: Loc = (0, 0)

    def __repr__(self) -> str:
        return f"GuessDeclNode({self.name})"


@dataclass
class LetDeclNode(Stmt):
    type_kind: TypeKind
    name: str
    value: Expr

    def __repr__(self) -> str:
        return f"LetDeclNode({self.type_kind.value}, {self.name})"


@dataclass
class AssignmentNode(Stmt):
    name: str
    value: Expr

    def __repr__(self) -> str:
        return f"AssignmentNode({self.name})"


@dataclass
class ShowNode(Stmt):
    args: List[Expr]
    loc: Loc = (0, 0)

    def __repr__(self) -> str:
        return f"ShowNode({len(self.args)} args)"


@dataclass
class ReturnNode(Stmt):
    value: Expr

    def __repr__(self) -> str:
        return "ReturnNode()"


@dataclass
class BreakNode(Stmt):
    def __repr__(self) -> str:
        return "BreakNode()"


@dataclass
class WhenNode(Stmt):
    cond: Expr
    body: BlockNode
    else_block: Optional[Union[BlockNode, "WhenNode"]] = None
    loc: Loc = (0, 0)

    def __repr__(self) -> str:
        return "WhenNode()"


@dataclass
class MatchCaseNode:
    pattern: Expr
    body: BlockNode


@dataclass
class MatchNode(Stmt):
    value: Expr
    cases: List[MatchCaseNode]
    else_block: Optional[BlockNode] = None

    def __repr__(self) -> str:
        return f"MatchNode({len(self.cases)} cases)"


@dataclass
class FlowCaseNode:
    cond: Expr
    body: BlockNode


@dataclass
class FlowNode(Stmt):
    cases: List[FlowCaseNode]
    else_block: Optional[BlockNode] = None

    def __repr__(self) -> str:
        return f"FlowNode({len(self.cases)} cases)"


@dataclass
class LoopNode(Stmt):
    variant: LoopVariant
    body: BlockNode

    def __repr__(self) -> str:
        return "LoopNode()"


@dataclass
class EachNode(Stmt):
    item_name: str
    list_name: str
    body: BlockNode

    def __repr__(self) -> str:
        return f"EachNode({self.item_name} in {self.list_name})"


@dataclass
class TaskDeclNode(Stmt):
    name: str
    params: List[ParamNode]
    body: BlockNode
    loc: Loc = (0, 0)

    def __repr__(self) -> str:
        return f"TaskDeclNode({self.name})"


@dataclass
class ExprStmtNode(Stmt):
    """Statement that is just an expression (e.g. last expression in block for return value)."""
    expr: Expr

    def __repr__(self) -> str:
        return f"ExprStmtNode({self.expr!r})"


@dataclass
class EndNode(Stmt):
    code: int

    def __repr__(self) -> str:
        return f"EndNode({self.code})"


# ---------------------------------------------------------------------------
# Root / program level
# ---------------------------------------------------------------------------

@dataclass
class StartNode:
    body: BlockNode

    def __repr__(self) -> str:
        return "StartNode()"


@dataclass
class ProgramNode:
    tasks: List[TaskDeclNode]
    start: StartNode

    def __repr__(self) -> str:
        return f"ProgramNode({len(self.tasks)} tasks)"
