"""
Rynx 2.0 Parser Errors — RX1xx. First error only.
"""

from atomc.errors.base_error import RynxError
from atomc.compiler.lexer.token import Token, TokenKind


def rx101_syntax_error(file: str, line: int, column: int, snippet: str, detail: str = "") -> RynxError:
    return RynxError(
        code="RX101",
        name="SyntaxError",
        message=f"Invalid syntax{': ' + detail if detail else ''}".strip(),
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )


def rx102_unexpected_token(file: str, line: int, column: int, snippet: str, got: str) -> RynxError:
    return RynxError(
        code="RX102",
        name="UnexpectedToken",
        message=f"Unexpected token: {got}",
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )


def rx103_missing_brace(file: str, line: int, column: int, snippet: str) -> RynxError:
    return RynxError(
        code="RX103",
        name="MissingBrace",
        message="Missing brace",
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )


def rx210_invalid_end_value(file: str, line: int, column: int, snippet: str) -> RynxError:
    return RynxError(
        code="RX210",
        name="InvalidEndValue",
        message="end must be 0 or 1",
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )


def rx211_missing_start_block(file: str, line: int, column: int, snippet: str) -> RynxError:
    return RynxError(
        code="RX211",
        name="MissingStartBlock",
        message="Exactly one start block required",
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )


def rx213_execution_block_missing(file: str, line: int, column: int, snippet: str) -> RynxError:
    """No start/end — execution structure error, not syntax error."""
    return RynxError(
        code="RX213",
        name="ExecutionBlockMissing",
        message="Execution block missing",
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )


def error_from_token(token: Token, file: str, message: str, code: str = "RX102") -> RynxError:
    snippet = str(token.value) if token.value is not None else (token.kind.value or "")
    if len(snippet) > 80:
        snippet = snippet[:77] + "..."
    return RynxError(
        code=code,
        name="UnexpectedToken",
        message=message,
        file=file,
        line=token.line,
        column=token.column,
        snippet=snippet,
    )
