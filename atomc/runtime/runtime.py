"""
Rynx 2.0 Runtime — AST interpreter. Deterministic. No bytecode.
Runtime errors: print diagnostic, exit 1. End 0 → success, end 1 → graceful fail.
"""

from typing import Any, Optional, List
import sys

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
    LoopVariantKind,
)
from atomc.runtime.execution_context import ExecutionContext
from atomc.runtime.runtime_errors import (
    rx501_index_out_of_bounds,
    rx502_division_by_zero,
    rx504_input_parse_fail,
)
from atomc.errors.base_error import RynxError
from atomc.errors.error_formatter import format_runtime_error
from atomc.errors.snippets import get_line_snippet


class ProgramExit(Exception):
    """Normal or graceful program exit (end 0 or end 1)."""
    def __init__(self, code: int) -> None:
        self.code = code


class RuntimeBreak(Exception):
    """Break out of loop."""
    pass


def _get_loc(node: Any) -> tuple:
    if hasattr(node, "loc") and getattr(node, "loc", (0, 0)) != (0, 0):
        return node.loc
    return (1, 1)


class Interpreter:
    """Execute validated AST. First runtime error → print, raise, exit 1."""

    def __init__(self, program: ProgramNode, filename: str = "main.ryx", source: Optional[str] = None) -> None:
        self.program = program
        self.ctx = ExecutionContext(program)
        self.filename = filename
        self.source = source

    def run(self) -> int:
        """Execute start block. Return exit code (0 or 1)."""
        try:
            self._execute_block(self.program.start.body)
            return 0
        except ProgramExit as e:
            return e.code
        except RynxError as e:
            format_runtime_error(e, sys.stderr)
            return 1

    def _snippet(self, line: int) -> str:
        return get_line_snippet(self.source, line) if self.source else ""

    def _execute_block(self, block: BlockNode) -> Any:
        self.ctx.push_scope()
        result = None
        for stmt in block.statements:
            res = self._execute_statement(stmt)
            if res is not None:
                result = res
        self.ctx.pop_scope()
        return result

    def _execute_statement(self, stmt: Stmt) -> Any:
        if isinstance(stmt, VariableDeclNode):
            val = self._eval(stmt.value)
            self.ctx.declare(stmt.name, val)
            return None
        if isinstance(stmt, GuessDeclNode):
            val = self._eval(stmt.value)
            self.ctx.declare(stmt.name, val)
            return None
        if isinstance(stmt, LetDeclNode):
            val = self._eval(stmt.value)
            self.ctx.declare(stmt.name, val)
            return None
        if isinstance(stmt, AssignmentNode):
            val = self._eval(stmt.value)
            self.ctx.set(stmt.name, val)
            return None
        if isinstance(stmt, ShowNode):
            parts = [str(self._eval(a)) for a in stmt.args]
            print("".join(parts))
            return None
        if isinstance(stmt, ReturnNode):
            raise NotImplementedError("Return only in task call")
        if isinstance(stmt, BreakNode):
            raise RuntimeBreak()
        if isinstance(stmt, WhenNode):
            cond = self._eval(stmt.cond)
            if cond:
                return self._execute_block(stmt.body)
            elif stmt.else_block:
                if isinstance(stmt.else_block, WhenNode):
                    return self._execute_statement(stmt.else_block)
                return self._execute_block(stmt.else_block)
            return None
        if isinstance(stmt, MatchNode):
            val = self._eval(stmt.value)
            for case in stmt.cases:
                if self._match_pattern(val, case.pattern):
                    return self._execute_block(case.body)
            if stmt.else_block:
                return self._execute_block(stmt.else_block)
            return None
        if isinstance(stmt, FlowNode):
            for case in stmt.cases:
                if self._eval(case.cond):
                    return self._execute_block(case.body)
            if stmt.else_block:
                return self._execute_block(stmt.else_block)
            return None
        if isinstance(stmt, LoopNode):
            self._execute_loop(stmt)
            return None
        if isinstance(stmt, EachNode):
            lst = self.ctx.get(stmt.list_name)
            for item in lst:
                self.ctx.push_scope()
                self.ctx.declare(stmt.item_name, item)
                try:
                    for s in stmt.body.statements:
                        self._execute_statement(s)
                except RuntimeBreak:
                    self.ctx.pop_scope()
                    raise
                self.ctx.pop_scope()
            return None
        if isinstance(stmt, ExprStmtNode):
            return self._eval(stmt.expr)
        if isinstance(stmt, EndNode):
            raise ProgramExit(stmt.code)
        return None

    def _execute_loop(self, node: LoopNode) -> None:
        v = node.variant
        if v.kind == LoopVariantKind.INFINITE:
            while True:
                self.ctx.push_scope()
                try:
                    for stmt in node.body.statements:
                        self._execute_statement(stmt)
                except RuntimeBreak:
                    self.ctx.pop_scope()
                    return
                except ProgramExit:
                    self.ctx.pop_scope()
                    raise
                self.ctx.pop_scope()
            return
        if v.kind == LoopVariantKind.RANGE and v.range_expr:
            start = int(self._eval(v.range_expr.start))
            end = int(self._eval(v.range_expr.end))
            step = int(self._eval(v.range_expr.step)) if v.range_expr.step else (1 if end >= start else -1)
            if step == 0:
                step = 1
            self.ctx.push_scope()
            try:
                i = start
                while (step > 0 and i <= end) or (step < 0 and i >= end):
                    self.ctx.declare(v.name, i)
                    try:
                        for stmt in node.body.statements:
                            self._execute_statement(stmt)
                    except RuntimeBreak:
                        break
                    i += step
            finally:
                self.ctx.pop_scope()
            return
        if v.kind == LoopVariantKind.LIST and v.list_expr:
            lst = self._eval(v.list_expr)
            self.ctx.push_scope()
            try:
                for item in lst:
                    self.ctx.declare(v.name, item)
                    try:
                        for stmt in node.body.statements:
                            self._execute_statement(stmt)
                    except RuntimeBreak:
                        break
            finally:
                self.ctx.pop_scope()
            return

    def _match_pattern(self, value: Any, pattern: Expr) -> bool:
        if isinstance(pattern, NumLiteral):
            return value == pattern.value
        if isinstance(pattern, TextLiteral):
            return value == pattern.value
        if isinstance(pattern, BoolLiteral):
            return value == pattern.value
        if isinstance(pattern, RangeExpr):
            try:
                start = int(self._eval(pattern.start))
                end = int(self._eval(pattern.end))
                if isinstance(value, (int, float)):
                    return start <= value <= end
            except (TypeError, ValueError):
                pass
            return False
        return False

    def _eval(self, expr: Expr) -> Any:
        if isinstance(expr, NumLiteral):
            return expr.value
        if isinstance(expr, TextLiteral):
            return expr.value
        if isinstance(expr, BoolLiteral):
            return expr.value
        if isinstance(expr, VariableExpr):
            return self.ctx.get(expr.name)
        if isinstance(expr, BinaryExpr):
            return self._eval_binary(expr)
        if isinstance(expr, UnaryExpr):
            return self._eval_unary(expr)
        if isinstance(expr, CallExpr):
            return self._eval_call(expr)
        if isinstance(expr, IndexExpr):
            return self._eval_index(expr)
        if isinstance(expr, RangeExpr):
            return self._eval_range(expr)
        if isinstance(expr, BlockExpr):
            self.ctx.push_scope()
            result = None
            for stmt in expr.body.statements:
                if isinstance(stmt, ExprStmtNode):
                    result = self._eval(stmt.expr)
                else:
                    self._execute_statement(stmt)
            self.ctx.pop_scope()
            return result
        raise RuntimeError(f"Unknown expression: {type(expr)}")

    def _eval_binary(self, expr: BinaryExpr) -> Any:
        left = self._eval(expr.left)
        right = self._eval(expr.right)
        if expr.op == BinaryOp.ADD:
            return left + right
        if expr.op == BinaryOp.SUB:
            return left - right
        if expr.op == BinaryOp.MUL:
            return left * right
        if expr.op == BinaryOp.DIV:
            if right == 0:
                line, col = _get_loc(expr)
                raise rx502_division_by_zero(
                    self.filename, line, col, self._snippet(line)
                )
            return left / right if isinstance(left, float) or isinstance(right, float) else left // right
        if expr.op == BinaryOp.MOD:
            if right == 0:
                line, col = _get_loc(expr)
                raise rx502_division_by_zero(
                    self.filename, line, col, self._snippet(line)
                )
            return left % right
        if expr.op == BinaryOp.LT:
            return left < right
        if expr.op == BinaryOp.GT:
            return left > right
        if expr.op == BinaryOp.LE:
            return left <= right
        if expr.op == BinaryOp.GE:
            return left >= right
        if expr.op == BinaryOp.EQ:
            return left == right
        if expr.op == BinaryOp.NE:
            return left != right
        if expr.op == BinaryOp.AND:
            return bool(left and right)
        if expr.op == BinaryOp.OR:
            return bool(left or right)
        raise RuntimeError(f"Unknown binary op: {expr.op}")

    def _eval_unary(self, expr: UnaryExpr) -> Any:
        val = self._eval(expr.expr)
        if expr.op == UnaryOp.NOT:
            return not val
        if expr.op == UnaryOp.NEG:
            return -val
        return val

    def _eval_call(self, expr: CallExpr) -> Any:
        name = expr.name
        if name == "input_text":
            return input()
        if name == "input_num":
            try:
                return int(input())
            except ValueError:
                line, col = expr.loc
                raise rx504_input_parse_fail(
                    self.filename, line, col, self._snippet(line), "expected integer"
                )
        if name == "input_dec":
            try:
                return float(input())
            except ValueError:
                line, col = expr.loc
                raise rx504_input_parse_fail(
                    self.filename, line, col, self._snippet(line), "expected number"
                )
        if name == "input_yes":
            s = input().strip().lower()
            if s in ("true", "yes", "1"):
                return True
            if s in ("false", "no", "0"):
                return False
            line, col = expr.loc
            raise rx504_input_parse_fail(
                self.filename, line, col, self._snippet(line), "expected true/false"
            )
        if name == "len":
            x = self._eval(expr.args[0])
            return len(x)
        if name == "split":
            s = self._eval(expr.args[0])
            return s.split()
        if name == "join":
            lst = self._eval(expr.args[0])
            return "".join(str(x) for x in lst)
        if name == "round":
            return round(self._eval(expr.args[0]))
        if name == "max":
            return max(self._eval(a) for a in expr.args)
        if name == "min":
            return min(self._eval(a) for a in expr.args)
        if name == "rand":
            import random
            return random.randint(0, 100)
        task = self.ctx.get_task(name)
        if task is None:
            raise RuntimeError(f"Task not found: {name}")
        args = [self._eval(a) for a in expr.args]
        self.ctx.push_scope()
        for param, arg in zip(task.params, args):
            self.ctx.declare(param.name, arg)
        result = None
        try:
            for stmt in task.body.statements:
                if isinstance(stmt, ReturnNode):
                    result = self._eval(stmt.value)
                    break
                res = self._execute_statement(stmt)
                if res is not None:
                    result = res
        finally:
            self.ctx.pop_scope()
        return result

    def _eval_index(self, expr: IndexExpr) -> Any:
        target = self._eval(expr.target)
        index = int(self._eval(expr.index))
        if index < 0 or index >= len(target):
            line, col = _get_loc(expr)
            raise rx501_index_out_of_bounds(
                self.filename, line, col, self._snippet(line),
                index, len(target) - 1
            )
        return target[index]

    def _eval_range(self, expr: RangeExpr) -> List[int]:
        start = int(self._eval(expr.start))
        end = int(self._eval(expr.end))
        step = int(self._eval(expr.step)) if expr.step else (1 if end >= start else -1)
        if step == 0:
            step = 1
        result = []
        i = start
        while (step > 0 and i <= end) or (step < 0 and i >= end):
            result.append(i)
            i += step
        return result
