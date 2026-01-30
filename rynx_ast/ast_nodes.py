from typing import List, Optional, Any, Union
from dataclasses import dataclass

@dataclass
class RynxNode:
    """Base class for all AST nodes with position tracking for RX diagnostics."""
    line: int
    column: int

# --- ROOT NODES ---

@dataclass
class Program(RynxNode):
    tasks: List['TaskDecl']
    start_block: 'StartNode'

@dataclass
class StartNode(RynxNode):
    statements: List['Statement']
    exit_statement: 'EndNode'

# --- STATEMENTS ---

class Statement(RynxNode): pass

@dataclass
class VariableDecl(Statement):
    name: str
    var_type: str  # 'num', 'dec', 'text', 'yes'
    expression: 'ExprNode'
    is_let: bool = False
    is_guess: bool = False

@dataclass
class TaskDecl(RynxNode):
    name: str
    params: List[dict] # List of {'name': str, 'type': str}
    return_type: str
    body: 'BlockNode'

@dataclass
class BlockNode(RynxNode):
    statements: List[Statement]

@dataclass
class EndNode(RynxNode):
    code: int  # Must be 0 or 1

# --- EXPRESSIONS ---

class ExprNode(RynxNode): pass

@dataclass
class BinaryExpr(ExprNode):
    left: ExprNode
    operator: str
    right: ExprNode

@dataclass
class UnaryExpr(ExprNode):
    operator: str
    expression: ExprNode

@dataclass
class Literal(ExprNode):
    value: Any
    kind: str # 'num', 'dec', 'text', 'yes'

@dataclass
class Identifier(ExprNode):
    name: str

@dataclass
class TaskCall(ExprNode):
    task_name: str
    arguments: List[ExprNode]

# --- CONTROL FLOW ---

@dataclass
class WhenStmt(Statement):
    condition: ExprNode
    then_branch: BlockNode
    else_branch: Optional[Union[BlockNode, 'WhenStmt']] = None

@dataclass
class LoopStmt(Statement):
    # 'range', 'list', 'infinite'
    variant: str
    iterator: Optional[str]
    range_target: Optional['RangeNode'] = None
    body: BlockNode

@dataclass
class RangeNode(RynxNode):
    start: ExprNode
    end: ExprNode
    step: Optional[ExprNode] = None