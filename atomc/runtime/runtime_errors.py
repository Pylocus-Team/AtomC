"""
Rynx 2.0 Runtime Errors — RX5xx. Graceful. Print and end 1.
"""

from atomc.errors.base_error import RynxError


def rx501_index_out_of_bounds(
    file: str, line: int, column: int, snippet: str,
    index: int, max_index: int
) -> RynxError:
    return RynxError(
        code="RX501",
        name="IndexOutOfBounds",
        message=f"Index {index} out of bounds (max {max_index})",
        file=file,
        line=line,
        column=column,
        snippet=snippet,
        expected=f"Index {index} out of bounds (max {max_index})",
    )


def rx502_division_by_zero(file: str, line: int, column: int, snippet: str) -> RynxError:
    return RynxError(
        code="RX502",
        name="DivisionByZero",
        message="Division by zero",
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )


def rx504_input_parse_fail(file: str, line: int, column: int, snippet: str, detail: str = "") -> RynxError:
    return RynxError(
        code="RX504",
        name="InputParseFail",
        message=f"Input parse failed{': ' + detail if detail else ''}".strip(),
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )
