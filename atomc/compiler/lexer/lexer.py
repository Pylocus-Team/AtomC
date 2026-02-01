"""
Rynx 2.0 Lexer — Tokenization only. No semantics. No types.
First error only. Deterministic. Every token has line, column, end_column.
"""

from typing import List, Optional

from atomc.compiler.lexer.token import Token, TokenKind, KEYWORDS
from atomc.compiler.lexer.lexer_errors import (
    rx103_missing_brace,
    rx104_invalid_character,
    rx105_invalid_literal,
)
from atomc.errors.base_error import RynxError
from atomc.errors.snippets import get_line_snippet


def lex(source: str, filename: str = "main.ryx") -> List[Token]:
    """
    Lex source into tokens. On first error, raise RynxError (RX1xx).
    No recovery. No cascading errors.
    """
    tokens: List[Token] = []
    i = 0
    line = 1
    column = 1
    n = len(source)

    def current_char() -> str:
        if i >= n:
            return ""
        return source[i]

    def peek_char(offset: int = 1) -> str:
        if i + offset >= n:
            return ""
        return source[i + offset]

    def advance() -> str:
        nonlocal i, column
        if i >= n:
            return ""
        c = source[i]
        i += 1
        if c == "\n":
            line += 1
            column = 1
        else:
            column += 1
        return c

    def skip_whitespace() -> None:
        nonlocal i, line, column
        while i < n and source[i] in " \t\n\r":
            if source[i] == "\n":
                line += 1
                column = 1
            else:
                column += 1
            i += 1

    def skip_line_comment() -> None:
        nonlocal i, line, column
        while i < n and source[i] != "\n":
            i += 1
            column += 1
        if i < n:
            i += 1
            line += 1
            column = 1

    def skip_block_comment() -> Optional[RynxError]:
        nonlocal i, line, column
        i += 2
        column += 2
        while i < n:
            if source[i : i + 2] == "*/":
                i += 2
                column += 2
                return None
            if source[i] == "\n":
                line += 1
                column = 1
            else:
                column += 1
            i += 1
        snippet = get_line_snippet(source, line)
        return rx103_missing_brace(filename, line, column, snippet)

    def emit(kind: TokenKind, value: Optional[object] = None, start_col: Optional[int] = None, end_col: Optional[int] = None) -> None:
        sc = start_col if start_col is not None else column
        ec = end_col if end_col is not None else column
        tokens.append(
            Token(kind=kind, value=value, line=line, column=sc, end_column=ec)
        )

    while i < n:
        skip_whitespace()
        if i >= n:
            break

        start_line = line
        start_col = column
        c = source[i]

        if c == "/" and peek_char() == "/":
            skip_line_comment()
            continue
        if c == "/" and peek_char() == "*":
            err = skip_block_comment()
            if err is not None:
                raise err
            continue

        if c in " \t\n\r":
            advance()
            continue

        if c.isalpha() or c == "_":
            start = i
            while i < n and (source[i].isalnum() or source[i] == "_"):
                advance()
            if i > start:
                raw = source[start:i]
                end_col = column
                if raw in KEYWORDS:
                    emit(KEYWORDS[raw], None, start_col, end_col)
                else:
                    emit(TokenKind.IDENT, raw, start_col, end_col)
            continue

        if c.isdigit() or (c == "-" and i + 1 < n and source[i + 1].isdigit()):
            neg = c == "-"
            if neg:
                advance()
                start_col = column
            start = i
            while i < n and source[i].isdigit():
                advance()
            if i < n and source[i] == "." and i + 1 < n and source[i + 1].isdigit():
                advance()
                while i < n and source[i].isdigit():
                    advance()
                raw = source[start:i]
                try:
                    val = float(raw)
                    if neg:
                        val = -val
                    emit(TokenKind.NUM_LIT, val, start_col, column)
                except ValueError:
                    snippet = get_line_snippet(source, line)
                    raise rx105_invalid_literal(filename, line, start_col, snippet, raw)
            else:
                raw = source[start:i]
                try:
                    val = int(raw)
                    if neg:
                        val = -val
                    emit(TokenKind.NUM_LIT, val, start_col, column)
                except ValueError:
                    snippet = get_line_snippet(source, line)
                    raise rx105_invalid_literal(filename, line, start_col, snippet, raw)
            continue

        if c == '"':
            advance()
            start = i
            sb: List[str] = []
            while i < n and source[i] != '"':
                if source[i] == "\\":
                    advance()
                    if i >= n:
                        snippet = get_line_snippet(source, line)
                        raise rx105_invalid_literal(filename, line, column, snippet, "unterminated escape")
                    esc = source[i]
                    advance()
                    if esc == "n":
                        sb.append("\n")
                    elif esc == "t":
                        sb.append("\t")
                    elif esc == '"':
                        sb.append('"')
                    elif esc == "\\":
                        sb.append("\\")
                    else:
                        snippet = get_line_snippet(source, line)
                        raise rx105_invalid_literal(filename, line, column, snippet, f"bad escape \\{esc}")
                else:
                    sb.append(source[i])
                    advance()
            if i >= n:
                snippet = get_line_snippet(source, line)
                raise rx105_invalid_literal(filename, line, start_col, snippet, "unclosed string")
            advance()
            s = "".join(sb)
            if len(s) > 1024:
                snippet = get_line_snippet(source, line)
                raise rx105_invalid_literal(filename, line, start_col, snippet, "text max 1024 chars")
            emit(TokenKind.TEXT_LIT, s, start_col, column)
            continue

        if c == "." and peek_char() == ".":
            advance()
            advance()
            emit(TokenKind.OP_DOTDOT, None, start_col, column)
            continue
        if c == "&" and peek_char() == "&":
            advance()
            advance()
            emit(TokenKind.OP_AND, None, start_col, column)
            continue
        if c == "|" and peek_char() == "|":
            advance()
            advance()
            emit(TokenKind.OP_OR, None, start_col, column)
            continue
        if c == "=" and peek_char() == "=":
            advance()
            advance()
            emit(TokenKind.OP_EQ, None, start_col, column)
            continue
        if c == "!" and peek_char() == "=":
            advance()
            advance()
            emit(TokenKind.OP_NE, None, start_col, column)
            continue
        if c == "<" and peek_char() == "=":
            advance()
            advance()
            emit(TokenKind.OP_LE, None, start_col, column)
            continue
        if c == ">" and peek_char() == "=":
            advance()
            advance()
            emit(TokenKind.OP_GE, None, start_col, column)
            continue

        single: dict[str, TokenKind] = {
            "+": TokenKind.OP_ADD,
            "-": TokenKind.OP_SUB,
            "*": TokenKind.OP_MUL,
            "/": TokenKind.OP_DIV,
            "%": TokenKind.OP_MOD,
            "<": TokenKind.OP_LT,
            ">": TokenKind.OP_GT,
            "!": TokenKind.OP_NOT,
            "=": TokenKind.OP_ASSIGN,
            "{": TokenKind.LBRACE,
            "}": TokenKind.RBRACE,
            "(": TokenKind.LPAREN,
            ")": TokenKind.RPAREN,
            "[": TokenKind.LBRACK,
            "]": TokenKind.RBRACK,
            ",": TokenKind.COMMA,
            ";": TokenKind.SEMI,
            ":": TokenKind.COLON,
        }
        if c in single:
            advance()
            emit(single[c], None, start_col, column)
            continue

        snippet = get_line_snippet(source, line)
        raise rx104_invalid_character(filename, line, start_col, snippet, c)

    tokens.append(Token(kind=TokenKind.EOF, line=line, column=column, end_column=column))
    return tokens
