"""
Rynx 2.0 Lexer Errors — RX1xx. First error only. No recovery.
"""

from atomc.errors.base_error import RynxError


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


def rx104_invalid_character(file: str, line: int, column: int, snippet: str, char: str) -> RynxError:
    return RynxError(
        code="RX104",
        name="InvalidCharacter",
        message=f"Invalid character: {repr(char)}",
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )


def rx105_invalid_literal(file: str, line: int, column: int, snippet: str, detail: str = "") -> RynxError:
    return RynxError(
        code="RX105",
        name="InvalidLiteral",
        message=f"Invalid literal{': ' + detail if detail else ''}".strip(),
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )
