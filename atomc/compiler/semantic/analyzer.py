"""
Rynx 2.0 Semantic Analyzer — Scope, types, return validation.
First error only. Deterministic. No recovery.
"""

from typing import Optional, Dict, Any

from atomc.ast.ast_nodes import (
    ProgramNode,
    StartNode,
    BlockNode,
    Stmt,
    Expr,
    TypeKind,
    BinaryOp,
    UnaryOp,
    VariableDeclNode,
    GuessDeclNode,
    LetDeclNode,
    AssignmentNode,
    ShowNode,
    ReturnNode,
    BreakNode,
    WhenNode,
    MatchNode,
    FlowNode,
    LoopNode,
    EachNode,
    TaskDeclNode,
    ExprStmtNode,
    EndNode,
    NumLiteral,
    TextLiteral,
    BoolLiteral,
    VariableExpr,
    BinaryExpr,
    UnaryExpr,
    CallExpr,
    IndexExpr,
    RangeExpr,
    BlockExpr,
)
from atomc.compiler.semantic.scope import ScopeStack
from atomc.compiler.semantic.symbol_table import SymbolTable, TaskSignature
from atomc.compiler.semantic.type_system import (
    type_kind_to_str,
    is_numeric,
    is_list_type,
    element_type,
    comparable,
    arithmetic_result,
    concat_result,
    logic_operand,
    condition_type,
)
from atomc.compiler.semantic.semantic_errors import (
    rx201_type_mismatch,
    rx202_invalid_operator,
    rx203_missing_return,
    rx204_undefined_variable,
    rx205_invalid_task_call,
    rx206_invalid_condition,
    rx207_invalid_break,
    rx208_redeclaration,
    rx209_empty_task_body,
    rx212_show_requires_arg,
)
from atomc.errors.base_error import RynxError
from atomc.errors.snippets import get_line_snippet


def _get_loc(node: Any) -> tuple:
    if hasattr(node, "loc") and getattr(node, "loc", (0, 0)) != (0, 0):
        return node.loc
    return (1, 1)


def _snippet(source: Optional[str], line: int) -> str:
    if source:
        return get_line_snippet(source, line)
    return ""


class SemanticAnalyzer:
    """Single-pass semantic analysis. First error only."""

    def __init__(self, filename: str = "main.ryx", source: Optional[str] = None) -> None:
        self.filename = filename
        self.source = source
        self.symbol_table = SymbolTable()
        self.scope = ScopeStack()
        self.guess_types: Dict[str, TypeKind] = {}
        self.in_loop_depth = 0

    def analyze(self, program: ProgramNode) -> None:
        """Run semantic analysis. Raise RynxError on first error."""
        for task in program.tasks:
            self._register_task(task)
        for task in program.tasks:
            self._analyze_task(task)
        self._analyze_start(program.start)

    def _register_task(self, task: TaskDeclNode) -> None:
        self.symbol_table.register_task(task.name, task.params, returns_value=True)

    def _analyze_start(self, start: StartNode) -> None:
        self.scope.push()
        self._analyze_block(start.body)
        self.scope.pop()

    def _analyze_task(self, task: TaskDeclNode) -> None:
        self.scope.push()
        for p in task.params:
            if self.scope.has_local(p.name):
                line, col = _get_loc(task)
                raise rx208_redeclaration(
                    self.filename, line, col,
                    _snippet(self.source, line), p.name
                )
            self.scope.declare(p.name, p.type_kind, is_let=False)
        if not task.body.statements:
            line, col = _get_loc(task)
            raise rx209_empty_task_body(
                self.filename, line, col,
                _snippet(self.source, line), task.name
            )
        self._analyze_block(task.body)
        self._check_task_returns(task)
        sig = self.symbol_table.get_task(task.name)
        if sig and sig.return_type is None:
            sig.return_type = self._task_return_type(task)
        self.scope.pop()

    def _task_return_type(self, task: TaskDeclNode) -> TypeKind:
        """Infer return type from last statement."""
        stmts = task.body.statements
        if not stmts:
            return TypeKind.NUM
        last = stmts[-1]
        if isinstance(last, ReturnNode):
            return self._check_expression(last.value)
        if isinstance(last, ExprStmtNode):
            return self._check_expression(last.expr)
        if isinstance(last, WhenNode) and last.else_block:
            return self._block_last_type(last.body)
        return TypeKind.NUM

    def _block_last_type(self, block: BlockNode) -> TypeKind:
        if not block.statements:
            return TypeKind.NUM
        last = block.statements[-1]
        if isinstance(last, ReturnNode):
            return self._check_expression(last.value)
        if isinstance(last, ExprStmtNode):
            return self._check_expression(last.expr)
        return TypeKind.NUM

    def _check_task_returns(self, task: TaskDeclNode) -> None:
        """Task must return a value: explicit return or last expression."""
        stmts = task.body.statements
        if not stmts:
            return
        last = stmts[-1]
        if isinstance(last, ReturnNode):
            return
        if isinstance(last, ExprStmtNode):
            return
        if isinstance(last, WhenNode):
            self._check_when_returns(last, task.name)
            return
        line, col = _get_loc(task.body)
        raise rx203_missing_return(
            self.filename, line, col,
            _snippet(self.source, line), task.name
        )

    def _check_when_returns(self, when: WhenNode, task_name: str) -> None:
        """When used as last stmt: both branches must return or end with expression."""
        has_body_return = self._block_returns_value(when.body)
        if when.else_block is None:
            line, col = _get_loc(when)
            raise rx203_missing_return(
                self.filename, line, col,
                _snippet(self.source, line), task_name
            )
        if isinstance(when.else_block, WhenNode):
            self._check_when_returns(when.else_block, task_name)
            return
        has_else_return = self._block_returns_value(when.else_block)
        if not has_body_return or not has_else_return:
            line, col = _get_loc(when)
            raise rx203_missing_return(
                self.filename, line, col,
                _snippet(self.source, line), task_name
            )

    def _block_returns_value(self, block: BlockNode) -> bool:
        if not block.statements:
            return False
        last = block.statements[-1]
        if isinstance(last, ReturnNode):
            return True
        if isinstance(last, ExprStmtNode):
            return True
        if isinstance(last, WhenNode):
            if last.else_block is None:
                return False
            if isinstance(last.else_block, WhenNode):
                return self._block_returns_value(last.body) and self._block_returns_value(last.else_block.body)
            return self._block_returns_value(last.body) and self._block_returns_value(last.else_block)
        return False

    def _analyze_block(self, block: BlockNode) -> None:
        self.scope.push()
        for stmt in block.statements:
            self._analyze_statement(stmt)
        self.scope.pop()

    def _analyze_statement(self, stmt: Stmt) -> None:
        if isinstance(stmt, VariableDeclNode):
            self._check_variable_decl(stmt)
            return
        if isinstance(stmt, GuessDeclNode):
            self._check_guess_decl(stmt)
            return
        if isinstance(stmt, LetDeclNode):
            self._check_let_decl(stmt)
            return
        if isinstance(stmt, AssignmentNode):
            self._check_assignment(stmt)
            return
        if isinstance(stmt, ShowNode):
            self._check_show(stmt)
            return
        if isinstance(stmt, ReturnNode):
            self._check_expression(stmt.value)
            return
        if isinstance(stmt, BreakNode):
            if self.in_loop_depth <= 0:
                line, col = _get_loc(stmt)
                raise rx207_invalid_break(
                    self.filename, line, col,
                    _snippet(self.source, line)
                )
            return
        if isinstance(stmt, WhenNode):
            self._check_when(stmt)
            return
        if isinstance(stmt, MatchNode):
            self._check_match(stmt)
            return
        if isinstance(stmt, FlowNode):
            self._check_flow(stmt)
            return
        if isinstance(stmt, LoopNode):
            self._check_loop(stmt)
            return
        if isinstance(stmt, EachNode):
            self._check_each(stmt)
            return
        if isinstance(stmt, ExprStmtNode):
            self._check_expression(stmt.expr)
            return
        if isinstance(stmt, EndNode):
            if stmt.code not in (0, 1):
                line, col = _get_loc(stmt)
                raise rx201_type_mismatch(
                    self.filename, line, col, _snippet(self.source, line),
                    "0 or 1", str(stmt.code)
                )
            return

    def _check_variable_decl(self, node: VariableDeclNode) -> None:
        if self.scope.has_local(node.name):
            line, col = _get_loc(node)
            raise rx208_redeclaration(
                self.filename, line, col,
                _snippet(self.source, line), node.name
            )
        value_type = self._check_expression(node.value)
        if value_type != node.type_kind:
            line, col = node.value.loc if hasattr(node.value, "loc") else _get_loc(node)
            snippet = _snippet(self.source, line)
            raise rx201_type_mismatch(
                self.filename, line, col, snippet,
                type_kind_to_str(node.type_kind), type_kind_to_str(value_type)
            )
        self.scope.declare(node.name, node.type_kind, is_let=False)

    def _check_guess_decl(self, node: GuessDeclNode) -> None:
        if self.scope.has_local(node.name):
            line, col = _get_loc(node)
            raise rx208_redeclaration(
                self.filename, line, col,
                _snippet(self.source, line), node.name
            )
        value_type = self._check_expression(node.value)
        self.guess_types[node.name] = value_type
        self.scope.declare(node.name, TypeKind.GUESS, is_let=False)

    def _check_let_decl(self, node: LetDeclNode) -> None:
        if self.scope.has_local(node.name):
            line, col = _get_loc(node)
            raise rx208_redeclaration(
                self.filename, line, col,
                _snippet(self.source, line), node.name
            )
        value_type = self._check_expression(node.value)
        if value_type != node.type_kind:
            line, col = _get_loc(node.value)
            raise rx201_type_mismatch(
                self.filename, line, col, _snippet(self.source, line),
                type_kind_to_str(node.type_kind), type_kind_to_str(value_type)
            )
        self.scope.declare(node.name, node.type_kind, is_let=True)

    def _check_assignment(self, node: AssignmentNode) -> None:
        info = self.scope.get(node.name)
        if info is None:
            line, col = _get_loc(node)
            raise rx204_undefined_variable(
                self.filename, line, col,
                _snippet(self.source, line), node.name
            )
        type_kind, _ = info
        value_type = self._check_expression(node.value)
        if type_kind == TypeKind.GUESS:
            if node.name not in self.guess_types:
                line, col = _get_loc(node)
                raise rx204_undefined_variable(
                    self.filename, line, col,
                    _snippet(self.source, line), node.name
                )
            locked = self.guess_types[node.name]
            if value_type != locked:
                line, col = _get_loc(node.value)
                raise rx201_type_mismatch(
                    self.filename, line, col, _snippet(self.source, line),
                    type_kind_to_str(locked), type_kind_to_str(value_type)
                )
        else:
            if value_type != type_kind:
                line, col = _get_loc(node.value)
                raise rx201_type_mismatch(
                    self.filename, line, col, _snippet(self.source, line),
                    type_kind_to_str(type_kind), type_kind_to_str(value_type)
                )

    def _check_show(self, node: ShowNode) -> None:
        if not node.args:
            line, col = _get_loc(node)
            raise rx212_show_requires_arg(
                self.filename, line, col,
                _snippet(self.source, line)
            )
        for a in node.args:
            self._check_expression(a)

    def _check_when(self, node: WhenNode) -> None:
        cond_type = self._check_expression(node.cond)
        if not condition_type(cond_type):
            line, col = _get_loc(node.cond)
            raise rx206_invalid_condition(
                self.filename, line, col,
                _snippet(self.source, line)
            )
        self._analyze_block(node.body)
        if node.else_block:
            if isinstance(node.else_block, WhenNode):
                self._check_when(node.else_block)
            else:
                self._analyze_block(node.else_block)

    def _check_match(self, node: MatchNode) -> None:
        self._check_expression(node.value)
        for case in node.cases:
            self._check_expression(case.pattern)
            self._analyze_block(case.body)
        if node.else_block:
            self._analyze_block(node.else_block)

    def _check_flow(self, node: FlowNode) -> None:
        for case in node.cases:
            cond_type = self._check_expression(case.cond)
            if not condition_type(cond_type):
                line, col = _get_loc(case.cond)
                raise rx206_invalid_condition(
                    self.filename, line, col,
                    _snippet(self.source, line)
                )
            self._analyze_block(case.body)
        if node.else_block:
            self._analyze_block(node.else_block)

    def _check_loop(self, node: LoopNode) -> None:
        from atomc.ast.ast_nodes import LoopVariantKind
        v = node.variant
        if v.kind == LoopVariantKind.RANGE and v.range_expr:
            self._check_expression(v.range_expr.start)
            self._check_expression(v.range_expr.end)
            if v.range_expr.step:
                self._check_expression(v.range_expr.step)
        elif v.kind == LoopVariantKind.LIST and v.list_expr:
            self._check_expression(v.list_expr)
        self.in_loop_depth += 1
        self.scope.push()
        if v.name:
            self.scope.declare(v.name, TypeKind.NUM, is_let=False)
        for stmt in node.body.statements:
            self._analyze_statement(stmt)
        self.scope.pop()
        self.in_loop_depth -= 1

    def _check_each(self, node: EachNode) -> None:
        info = self.scope.get(node.list_name)
        if info is None:
            line, col = _get_loc(node)
            raise rx204_undefined_variable(
                self.filename, line, col,
                _snippet(self.source, line), node.list_name
            )
        list_type, _ = info
        if not is_list_type(list_type):
            line, col = _get_loc(node)
            raise rx201_type_mismatch(
                self.filename, line, col, _snippet(self.source, line),
                "list type", type_kind_to_str(list_type)
            )
        elem = element_type(list_type)
        if elem is None:
            elem = TypeKind.NUM
        self.scope.push()
        self.scope.declare(node.item_name, elem, is_let=False)
        for stmt in node.body.statements:
            self._analyze_statement(stmt)
        self.scope.pop()

    def _check_expression(self, expr: Expr) -> TypeKind:
        if isinstance(expr, NumLiteral):
            if isinstance(expr.value, float):
                return TypeKind.DEC
            return TypeKind.NUM
        if isinstance(expr, TextLiteral):
            return TypeKind.TEXT
        if isinstance(expr, BoolLiteral):
            return TypeKind.YES
        if isinstance(expr, VariableExpr):
            info = self.scope.get(expr.name)
            if info is None:
                line, col = expr.loc
                raise rx204_undefined_variable(
                    self.filename, line, col,
                    _snippet(self.source, line), expr.name
                )
            return info[0]
        if isinstance(expr, BinaryExpr):
            return self._check_binary(expr)
        if isinstance(expr, UnaryExpr):
            return self._check_unary(expr)
        if isinstance(expr, CallExpr):
            return self._check_call(expr)
        if isinstance(expr, IndexExpr):
            return self._check_index(expr)
        if isinstance(expr, RangeExpr):
            self._check_expression(expr.start)
            self._check_expression(expr.end)
            if expr.step:
                self._check_expression(expr.step)
            return TypeKind.NUMS
        if isinstance(expr, BlockExpr):
            self.scope.push()
            last_type: Optional[TypeKind] = None
            for stmt in expr.body.statements:
                if isinstance(stmt, ExprStmtNode):
                    last_type = self._check_expression(stmt.expr)
                else:
                    self._analyze_statement(stmt)
            self.scope.pop()
            if last_type is None:
                line, col = _get_loc(expr)
                raise rx203_missing_return(
                    self.filename, line, col,
                    _snippet(self.source, line), ""
                )
            return last_type
        line, col = _get_loc(expr)
        raise rx202_invalid_operator(
            self.filename, line, col,
            _snippet(self.source, line), "unknown expression"
        )

    def _check_binary(self, expr: BinaryExpr) -> TypeKind:
        left_t = self._check_expression(expr.left)
        right_t = self._check_expression(expr.right)
        line, col = expr.loc
        snippet = _snippet(self.source, line)
        if expr.op in (BinaryOp.ADD, BinaryOp.SUB, BinaryOp.MUL, BinaryOp.DIV, BinaryOp.MOD):
            res = arithmetic_result(left_t, right_t)
            if res is not None:
                return res
            if expr.op == BinaryOp.ADD:
                concat = concat_result(left_t, right_t)
                if concat is not None:
                    return concat
            raise rx202_invalid_operator(
                self.filename, line, col, snippet,
                f"operator {expr.op.value} between {type_kind_to_str(left_t)} and {type_kind_to_str(right_t)}"
            )
        if expr.op in (BinaryOp.LT, BinaryOp.GT, BinaryOp.LE, BinaryOp.GE, BinaryOp.EQ, BinaryOp.NE):
            if not comparable(left_t, right_t):
                raise rx202_invalid_operator(
                    self.filename, line, col, snippet,
                    f"comparison between {type_kind_to_str(left_t)} and {type_kind_to_str(right_t)}"
                )
            return TypeKind.YES
        if expr.op in (BinaryOp.AND, BinaryOp.OR):
            if not logic_operand(left_t) or not logic_operand(right_t):
                raise rx206_invalid_condition(self.filename, line, col, snippet)
            return TypeKind.YES
        raise rx202_invalid_operator(self.filename, line, col, snippet, expr.op.value)

    def _check_unary(self, expr: UnaryExpr) -> TypeKind:
        t = self._check_expression(expr.expr)
        line, col = _get_loc(expr.expr)
        snippet = _snippet(self.source, line)
        if expr.op == UnaryOp.NOT:
            if not logic_operand(t):
                raise rx206_invalid_condition(self.filename, line, col, snippet)
            return TypeKind.YES
        if expr.op == UnaryOp.NEG:
            if not is_numeric(t):
                raise rx202_invalid_operator(
                    self.filename, line, col, snippet,
                    f"unary - requires num or dec, got {type_kind_to_str(t)}"
                )
            return t
        return t

    def _check_call(self, expr: CallExpr) -> TypeKind:
        name = expr.name
        if name == "input_text":
            if expr.args:
                line, col = expr.loc
                raise rx205_invalid_task_call(
                    self.filename, line, col, _snippet(self.source, line),
                    "input_text() takes no arguments"
                )
            return TypeKind.TEXT
        if name == "input_num":
            if expr.args:
                line, col = expr.loc
                raise rx205_invalid_task_call(
                    self.filename, line, col, _snippet(self.source, line),
                    "input_num() takes no arguments"
                )
            return TypeKind.NUM
        if name == "input_dec":
            if expr.args:
                line, col = expr.loc
                raise rx205_invalid_task_call(
                    self.filename, line, col, _snippet(self.source, line),
                    "input_dec() takes no arguments"
                )
            return TypeKind.DEC
        if name == "input_yes":
            if expr.args:
                line, col = expr.loc
                raise rx205_invalid_task_call(
                    self.filename, line, col, _snippet(self.source, line),
                    "input_yes() takes no arguments"
                )
            return TypeKind.YES
        if name == "len":
            if len(expr.args) != 1:
                line, col = expr.loc
                raise rx205_invalid_task_call(
                    self.filename, line, col, _snippet(self.source, line),
                    "len() takes exactly one argument"
                )
            self._check_expression(expr.args[0])
            return TypeKind.NUM
        if name == "split":
            if len(expr.args) != 1:
                line, col = expr.loc
                raise rx205_invalid_task_call(
                    self.filename, line, col, _snippet(self.source, line),
                    "split() takes exactly one argument"
                )
            t = self._check_expression(expr.args[0])
            if t != TypeKind.TEXT:
                line, col = _get_loc(expr.args[0])
                raise rx201_type_mismatch(
                    self.filename, line, col, _snippet(self.source, line),
                    "text", type_kind_to_str(t)
                )
            return TypeKind.TEXTS
        if name == "join":
            if len(expr.args) != 1:
                line, col = expr.loc
                raise rx205_invalid_task_call(
                    self.filename, line, col, _snippet(self.source, line),
                    "join() takes exactly one argument"
                )
            t = self._check_expression(expr.args[0])
            if not is_list_type(t):
                line, col = _get_loc(expr.args[0])
                raise rx201_type_mismatch(
                    self.filename, line, col, _snippet(self.source, line),
                    "list type", type_kind_to_str(t)
                )
            return TypeKind.TEXT
        if name == "round":
            if len(expr.args) != 1:
                line, col = expr.loc
                raise rx205_invalid_task_call(
                    self.filename, line, col, _snippet(self.source, line),
                    "round() takes exactly one argument"
                )
            t = self._check_expression(expr.args[0])
            if t != TypeKind.DEC:
                line, col = _get_loc(expr.args[0])
                raise rx201_type_mismatch(
                    self.filename, line, col, _snippet(self.source, line),
                    "dec", type_kind_to_str(t)
                )
            return TypeKind.NUM
        if name == "max" or name == "min":
            if not expr.args:
                line, col = expr.loc
                raise rx205_invalid_task_call(
                    self.filename, line, col, _snippet(self.source, line),
                    "max/min require at least one argument"
                )
            first = self._check_expression(expr.args[0])
            for a in expr.args[1:]:
                self._check_expression(a)
            return first if is_numeric(first) else TypeKind.NUM
        if name == "rand":
            if expr.args:
                line, col = expr.loc
                raise rx205_invalid_task_call(
                    self.filename, line, col, _snippet(self.source, line),
                    "rand() takes no arguments"
                )
            return TypeKind.NUM
        sig = self.symbol_table.get_task(name)
        if sig is None:
            line, col = expr.loc
            raise rx204_undefined_variable(
                self.filename, line, col,
                _snippet(self.source, line), name
            )
        if len(expr.args) != len(sig.params):
            line, col = expr.loc
            raise rx205_invalid_task_call(
                self.filename, line, col, _snippet(self.source, line),
                f"task {name} expects {len(sig.params)} arguments, got {len(expr.args)}"
            )
        for arg_expr, param in zip(expr.args, sig.params):
            arg_t = self._check_expression(arg_expr)
            if arg_t != param.type_kind:
                line, col = _get_loc(arg_expr)
                raise rx201_type_mismatch(
                    self.filename, line, col, _snippet(self.source, line),
                    type_kind_to_str(param.type_kind), type_kind_to_str(arg_t)
                )
        return sig.return_type if sig.return_type is not None else TypeKind.NUM

    def _check_index(self, expr: IndexExpr) -> TypeKind:
        target_t = self._check_expression(expr.target)
        index_t = self._check_expression(expr.index)
        line, col = _get_loc(expr)
        snippet = _snippet(self.source, line)
        if index_t != TypeKind.NUM:
            raise rx201_type_mismatch(
                self.filename, line, col, snippet,
                "num", type_kind_to_str(index_t)
            )
        if not is_list_type(target_t):
            raise rx201_type_mismatch(
                self.filename, line, col, snippet,
                "list type", type_kind_to_str(target_t)
            )
        elem = element_type(target_t)
        return elem if elem else TypeKind.NUM
