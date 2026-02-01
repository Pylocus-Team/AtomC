"""
Rynx 2.0 Parser — Build AST from token stream. EBNF-driven. First error only.
Strict phase separation. No recovery. Deterministic.
"""

from typing import List, Optional, Union

from atomc.ast.ast_nodes import (
    ProgramNode,
    StartNode,
    BlockNode,
    Stmt,
    Expr,
    TypeKind,
    BinaryOp,
    UnaryOp,
    LoopVariantKind,
    LoopVariant,
    ParamNode,
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
    VariableDeclNode,
    GuessDeclNode,
    LetDeclNode,
    AssignmentNode,
    ShowNode,
    ReturnNode,
    BreakNode,
    WhenNode,
    MatchNode,
    MatchCaseNode,
    FlowNode,
    FlowCaseNode,
    LoopNode,
    EachNode,
    TaskDeclNode,
    ExprStmtNode,
    EndNode,
)
from atomc.compiler.lexer.token import Token, TokenKind
from atomc.compiler.parser.parser_state import ParserState
from atomc.compiler.parser.parser_errors import (
    rx101_syntax_error,
    rx102_unexpected_token,
    rx210_invalid_end_value,
    rx213_execution_block_missing,
)
from atomc.errors.base_error import RynxError
from atomc.errors.snippets import get_line_snippet


# ---------------------------------------------------------------------------
# Type keyword → TypeKind
# ---------------------------------------------------------------------------
TYPE_KINDS: dict[TokenKind, TypeKind] = {
    TokenKind.KW_NUM: TypeKind.NUM,
    TokenKind.KW_DEC: TypeKind.DEC,
    TokenKind.KW_TEXT: TypeKind.TEXT,
    TokenKind.KW_YES: TypeKind.YES,
    TokenKind.KW_NUMS: TypeKind.NUMS,
    TokenKind.KW_TEXTS: TypeKind.TEXTS,
    TokenKind.KW_DECS: TypeKind.DECS,
    TokenKind.KW_YESS: TypeKind.YESS,
}

# ---------------------------------------------------------------------------
# Token → BinaryOp
# ---------------------------------------------------------------------------
BINARY_OPS: dict[TokenKind, BinaryOp] = {
    TokenKind.OP_ADD: BinaryOp.ADD,
    TokenKind.OP_SUB: BinaryOp.SUB,
    TokenKind.OP_MUL: BinaryOp.MUL,
    TokenKind.OP_DIV: BinaryOp.DIV,
    TokenKind.OP_MOD: BinaryOp.MOD,
    TokenKind.OP_LT: BinaryOp.LT,
    TokenKind.OP_GT: BinaryOp.GT,
    TokenKind.OP_LE: BinaryOp.LE,
    TokenKind.OP_GE: BinaryOp.GE,
    TokenKind.OP_EQ: BinaryOp.EQ,
    TokenKind.OP_NE: BinaryOp.NE,
    TokenKind.OP_AND: BinaryOp.AND,
    TokenKind.OP_OR: BinaryOp.OR,
}


def parse(tokens: List[Token], filename: str = "main.ryx", source: Optional[str] = None) -> ProgramNode:
    """Parse token stream into ProgramNode. On first error, raise RynxError (RX1xx)."""
    state = ParserState(tokens, filename, source)
    return _parse_program(state)


def _parse_program(state: ParserState) -> ProgramNode:
    tasks: List[TaskDeclNode] = []
    while state.check(TokenKind.KW_TASK):
        tasks.append(_parse_task_decl(state))
    if not state.check(TokenKind.KW_START):
        t = state.current()
        snippet = get_line_snippet(state.source, t.line) if state.source else str(t.kind.value or "eof")
        raise rx213_execution_block_missing(state.filename, t.line, t.column, snippet)
    state.advance()
    start_block = _parse_block(state, is_start_block=True)
    start_node = StartNode(body=start_block)
    return ProgramNode(tasks=tasks, start=start_node)


def _parse_block(state: ParserState, is_start_block: bool = False) -> BlockNode:
    state.expect(TokenKind.LBRACE)
    statements: List[Stmt] = []
    while not state.check(TokenKind.RBRACE) and not state.check(TokenKind.EOF):
        stmt = _parse_statement(state, is_start_block=is_start_block)
        statements.append(stmt)
        if is_start_block and isinstance(stmt, EndNode):
            break
    if not state.check(TokenKind.RBRACE):
        t = state.current()
        snippet = get_line_snippet(state.source, t.line) if state.source else (t.kind.value or "")
        raise rx102_unexpected_token(state.filename, t.line, t.column, snippet, str(t.kind.value or "eof"))
    state.advance()
    return BlockNode(statements=statements)


def _parse_statement(state: ParserState, is_start_block: bool = False) -> Stmt:
    t = state.current()
    if state.check(TokenKind.KW_BREAK):
        state.advance()
        state.expect(TokenKind.SEMI)
        return BreakNode()
    if state.check(TokenKind.KW_RETURN):
        state.advance()
        expr = _parse_expression(state)
        state.expect(TokenKind.SEMI)
        return ReturnNode(value=expr)
    if state.check(TokenKind.KW_END):
        state.advance()
        if not state.check(TokenKind.NUM_LIT):
            snippet = get_line_snippet(state.source, t.line) if state.source else "end"
            raise rx210_invalid_end_value(state.filename, t.line, t.column, snippet)
        val = state.advance().value
        if val not in (0, 1):
            snippet = get_line_snippet(state.source, t.line) if state.source else f"end {val};"
            raise rx210_invalid_end_value(state.filename, t.line, t.column, snippet)
        state.expect(TokenKind.SEMI)
        return EndNode(code=int(val))
    if state.check(TokenKind.KW_SHOW):
        return _parse_show(state)
    if state.check(TokenKind.KW_WHEN):
        return _parse_when(state)
    if state.check(TokenKind.KW_LOOP):
        return _parse_loop(state)
    if state.check(TokenKind.KW_EACH):
        return _parse_each(state)
    if state.check(TokenKind.KW_MATCH):
        return _parse_match(state)
    if state.check(TokenKind.KW_FLOW):
        return _parse_flow(state)
    if state.check(TokenKind.KW_GUESS):
        return _parse_guess_decl(state)
    if state.check(TokenKind.KW_LET):
        return _parse_let_decl(state)
    if state.check_any(TokenKind.KW_NUM, TokenKind.KW_DEC, TokenKind.KW_TEXT, TokenKind.KW_YES,
                      TokenKind.KW_NUMS, TokenKind.KW_TEXTS, TokenKind.KW_DECS, TokenKind.KW_YESS):
        return _parse_variable_decl(state)
    if state.check(TokenKind.IDENT):
        name = state.current().value
        if state.peek(1).kind == TokenKind.OP_ASSIGN:
            state.advance()
            state.advance()
            expr = _parse_expression(state)
            state.expect(TokenKind.SEMI)
            return AssignmentNode(name=name, value=expr)
        expr = _parse_expression(state)
        state.expect(TokenKind.SEMI)
        return ExprStmtNode(expr=expr)
    expr = _parse_expression(state)
    state.expect(TokenKind.SEMI)
    return ExprStmtNode(expr=expr)


def _parse_show(state: ParserState) -> ShowNode:
    state.expect(TokenKind.KW_SHOW)
    args: List[Expr] = [_parse_expression(state)]
    while state.check(TokenKind.COMMA):
        state.advance()
        args.append(_parse_expression(state))
    state.expect(TokenKind.SEMI)
    return ShowNode(args=args)


def _parse_when(state: ParserState) -> WhenNode:
    state.expect(TokenKind.KW_WHEN)
    cond = _parse_expression(state)
    body = _parse_block(state)
    else_block: Optional[Union[BlockNode, WhenNode]] = None
    if state.check(TokenKind.KW_ELSE):
        state.advance()
        if state.check(TokenKind.KW_WHEN):
            else_block = _parse_when(state)
        else:
            else_block = _parse_block(state)
    return WhenNode(cond=cond, body=body, else_block=else_block, loc=_expr_loc(cond))


def _parse_loop(state: ParserState) -> LoopNode:
    state.expect(TokenKind.KW_LOOP)
    if state.check(TokenKind.LBRACE):
        body = _parse_block(state)
        return LoopNode(variant=LoopVariant(kind=LoopVariantKind.INFINITE), body=body)
    name_tok = state.expect(TokenKind.IDENT)
    name = name_tok.value
    state.expect(TokenKind.KW_THRU)
    if state.check(TokenKind.IDENT):
        list_name = state.advance().value
        body = _parse_block(state)
        return LoopNode(
            variant=LoopVariant(kind=LoopVariantKind.LIST, name=name, list_expr=VariableExpr(name=list_name)),
            body=body,
        )
    # Range: expr .. expr [step expr]
    start_expr = _parse_expression(state)
    state.expect(TokenKind.OP_DOTDOT)
    end_expr = _parse_expression(state)
    step_expr: Optional[Expr] = None
    if state.check(TokenKind.KW_STEP):
        state.advance()
        step_expr = _parse_expression(state)
    range_expr = RangeExpr(start=start_expr, end=end_expr, step=step_expr)
    body = _parse_block(state)
    return LoopNode(
        variant=LoopVariant(kind=LoopVariantKind.RANGE, name=name, range_expr=range_expr),
        body=body,
    )


def _parse_each(state: ParserState) -> EachNode:
    state.expect(TokenKind.KW_EACH)
    item_name = state.expect(TokenKind.IDENT).value
    state.expect(TokenKind.KW_IN)
    list_name = state.expect(TokenKind.IDENT).value
    body = _parse_block(state)
    return EachNode(item_name=item_name, list_name=list_name, body=body)


def _parse_match(state: ParserState) -> MatchNode:
    state.expect(TokenKind.KW_MATCH)
    value = _parse_expression(state)
    state.expect(TokenKind.LBRACE)
    cases: List[MatchCaseNode] = []
    else_block: Optional[BlockNode] = None
    while not state.check(TokenKind.RBRACE) and not state.check(TokenKind.EOF):
        if state.check(TokenKind.KW_ELSE):
            state.advance()
            state.expect(TokenKind.COLON)
            else_block = _parse_block(state)
            break
        state.expect(TokenKind.KW_CASE)
        pattern = _parse_expression(state)
        state.expect(TokenKind.COLON)
        body = _parse_block(state)
        cases.append(MatchCaseNode(pattern=pattern, body=body))
    state.expect(TokenKind.RBRACE)
    return MatchNode(value=value, cases=cases, else_block=else_block)


def _parse_flow(state: ParserState) -> FlowNode:
    state.expect(TokenKind.KW_FLOW)
    state.expect(TokenKind.LBRACE)
    cases: List[FlowCaseNode] = []
    else_block: Optional[BlockNode] = None
    while not state.check(TokenKind.RBRACE) and not state.check(TokenKind.EOF):
        if state.check(TokenKind.KW_ELSE):
            state.advance()
            state.expect(TokenKind.COLON)
            else_block = _parse_block(state)
            break
        state.expect(TokenKind.KW_WHEN)
        cond = _parse_expression(state)
        state.expect(TokenKind.COLON)
        body = _parse_block(state)
        cases.append(FlowCaseNode(cond=cond, body=body))
    state.expect(TokenKind.RBRACE)
    return FlowNode(cases=cases, else_block=else_block)


def _parse_variable_decl(state: ParserState) -> VariableDeclNode:
    type_tok = state.advance()
    type_kind = TYPE_KINDS[type_tok.kind]
    name = state.expect(TokenKind.IDENT).value
    state.expect(TokenKind.OP_ASSIGN)
    value = _parse_expression(state)
    state.expect(TokenKind.SEMI)
    loc = _expr_loc(value)
    return VariableDeclNode(type_kind=type_kind, name=name, value=value, loc=loc)


def _parse_guess_decl(state: ParserState) -> GuessDeclNode:
    state.expect(TokenKind.KW_GUESS)
    name = state.expect(TokenKind.IDENT).value
    state.expect(TokenKind.OP_ASSIGN)
    value = _parse_expression(state)
    state.expect(TokenKind.SEMI)
    return GuessDeclNode(name=name, value=value, loc=_expr_loc(value))


def _parse_let_decl(state: ParserState) -> LetDeclNode:
    state.expect(TokenKind.KW_LET)
    type_tok = state.advance()
    type_kind = TYPE_KINDS[type_tok.kind]
    name = state.expect(TokenKind.IDENT).value
    state.expect(TokenKind.OP_ASSIGN)
    value = _parse_expression(state)
    state.expect(TokenKind.SEMI)
    return LetDeclNode(type_kind=type_kind, name=name, value=value)


def _parse_task_decl(state: ParserState) -> TaskDeclNode:
    task_tok = state.current()
    state.expect(TokenKind.KW_TASK)
    name = state.expect(TokenKind.IDENT).value
    state.expect(TokenKind.LPAREN)
    params: List[ParamNode] = []
    if not state.check(TokenKind.RPAREN):
        type_tok = state.advance()
        type_kind = TYPE_KINDS[type_tok.kind]
        pname = state.expect(TokenKind.IDENT).value
        params.append(ParamNode(type_kind=type_kind, name=pname))
        while state.check(TokenKind.COMMA):
            state.advance()
            type_tok = state.advance()
            type_kind = TYPE_KINDS[type_tok.kind]
            pname = state.expect(TokenKind.IDENT).value
            params.append(ParamNode(type_kind=type_kind, name=pname))
    state.expect(TokenKind.RPAREN)
    body = _parse_block(state)
    return TaskDeclNode(name=name, params=params, body=body, loc=_loc(state))


# ---------------------------------------------------------------------------
# Expressions — precedence: logical_or < logical_and < comparison < term < factor < unary < primary
# ---------------------------------------------------------------------------

def _parse_expression(state: ParserState) -> Expr:
    return _parse_logical_or(state)


def _expr_loc(expr: Expr) -> tuple:
    if hasattr(expr, "loc") and expr.loc != (0, 0):
        return expr.loc
    return (1, 1)


def _parse_logical_or(state: ParserState) -> Expr:
    left = _parse_logical_and(state)
    while state.check(TokenKind.OP_OR):
        op_tok = state.advance()
        right = _parse_logical_and(state)
        left = BinaryExpr(left=left, op=BinaryOp.OR, right=right, loc=_expr_loc(left))
    return left


def _parse_logical_and(state: ParserState) -> Expr:
    left = _parse_comparison(state)
    while state.check(TokenKind.OP_AND):
        state.advance()
        right = _parse_comparison(state)
        left = BinaryExpr(left=left, op=BinaryOp.AND, right=right, loc=_expr_loc(left))
    return left


def _parse_comparison(state: ParserState) -> Expr:
    left = _parse_term(state)
    while state.check_any(TokenKind.OP_LT, TokenKind.OP_GT, TokenKind.OP_LE, TokenKind.OP_GE, TokenKind.OP_EQ, TokenKind.OP_NE):
        op_tok = state.advance()
        op = BINARY_OPS[op_tok.kind]
        right = _parse_term(state)
        left = BinaryExpr(left=left, op=op, right=right, loc=_expr_loc(left))
    return left


def _parse_term(state: ParserState) -> Expr:
    left = _parse_factor(state)
    while state.check_any(TokenKind.OP_ADD, TokenKind.OP_SUB):
        op_tok = state.advance()
        op = BINARY_OPS[op_tok.kind]
        right = _parse_factor(state)
        left = BinaryExpr(left=left, op=op, right=right, loc=_expr_loc(left))
    return left


def _parse_factor(state: ParserState) -> Expr:
    left = _parse_unary(state)
    while state.check_any(TokenKind.OP_MUL, TokenKind.OP_DIV, TokenKind.OP_MOD):
        op_tok = state.advance()
        op = BINARY_OPS[op_tok.kind]
        right = _parse_unary(state)
        left = BinaryExpr(left=left, op=op, right=right, loc=_expr_loc(left))
    return left


def _parse_unary(state: ParserState) -> Expr:
    if state.check(TokenKind.OP_NOT):
        state.advance()
        expr = _parse_unary(state)
        return UnaryExpr(op=UnaryOp.NOT, expr=expr)
    if state.check(TokenKind.OP_SUB):
        state.advance()
        expr = _parse_unary(state)
        return UnaryExpr(op=UnaryOp.NEG, expr=expr)
    return _parse_primary(state)


def _loc(state: ParserState) -> tuple:
    t = state.current()
    return (t.line, t.column)


def _parse_primary(state: ParserState) -> Expr:
    t = state.current()
    if state.check(TokenKind.NUM_LIT):
        state.advance()
        val = t.value
        loc = (t.line, t.column)
        if isinstance(val, float):
            return NumLiteral(value=val, loc=loc)
        return NumLiteral(value=int(val), loc=loc)
    if state.check(TokenKind.TEXT_LIT):
        state.advance()
        return TextLiteral(value=t.value, loc=(t.line, t.column))
    if state.check(TokenKind.KW_TRUE):
        state.advance()
        return BoolLiteral(value=True)  # loc optional for literals
    if state.check(TokenKind.KW_FALSE):
        state.advance()
        return BoolLiteral(value=False)
    if state.check(TokenKind.KW_BLOCK):
        state.advance()
        body = _parse_block(state)
        return BlockExpr(body=body)
    if state.check(TokenKind.LPAREN):
        state.advance()
        expr = _parse_expression(state)
        state.expect(TokenKind.RPAREN)
        return expr
    if state.check(TokenKind.IDENT):
        ident_tok = state.current()
        name = state.advance().value
        loc = (ident_tok.line, ident_tok.column)
        if state.check(TokenKind.LPAREN):
            state.advance()
            args: List[Expr] = []
            if not state.check(TokenKind.RPAREN):
                args.append(_parse_expression(state))
                while state.check(TokenKind.COMMA):
                    state.advance()
                    args.append(_parse_expression(state))
            state.expect(TokenKind.RPAREN)
            return CallExpr(name=name, args=args, loc=loc)
        if state.check(TokenKind.LBRACK):
            state.advance()
            index = _parse_expression(state)
            state.expect(TokenKind.RBRACK)
            return IndexExpr(target=VariableExpr(name=name, loc=loc), index=index)
        return VariableExpr(name=name, loc=loc)
    t = state.current()
    snippet = get_line_snippet(state.source, t.line) if state.source else (t.kind.value or "")
    raise rx102_unexpected_token(state.filename, t.line, t.column, snippet, str(t.kind.value or "eof"))
