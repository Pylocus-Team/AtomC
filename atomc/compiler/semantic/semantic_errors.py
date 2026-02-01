"""
Rynx 2.0 Semantic Errors — RX2xx. First error only.
"""

from atomc.errors.base_error import RynxError


def rx201_type_mismatch(
    file: str, line: int, column: int, snippet: str,
    expected: str, found: str
) -> RynxError:
    return RynxError(
        code="RX201",
        name="TypeMismatchError",
        message="Type mismatch",
        file=file,
        line=line,
        column=column,
        snippet=snippet,
        expected=expected,
        found=found,
    )


def rx202_invalid_operator(
    file: str, line: int, column: int, snippet: str, detail: str = ""
) -> RynxError:
    return RynxError(
        code="RX202",
        name="InvalidOperator",
        message=f"Invalid operator{': ' + detail if detail else ''}".strip(),
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )


def rx203_missing_return(file: str, line: int, column: int, snippet: str, task_name: str = "") -> RynxError:
    return RynxError(
        code="RX203",
        name="MissingReturn",
        message=f"Missing return{': task ' + task_name if task_name else ''}".strip(),
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )


def rx204_undefined_variable(file: str, line: int, column: int, snippet: str, name: str) -> RynxError:
    return RynxError(
        code="RX204",
        name="UndefinedVariable",
        message=f"Undefined variable: {name}",
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )


def rx205_invalid_task_call(
    file: str, line: int, column: int, snippet: str, detail: str = ""
) -> RynxError:
    return RynxError(
        code="RX205",
        name="InvalidTaskCall",
        message=f"Invalid task call{': ' + detail if detail else ''}".strip(),
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )


def rx206_invalid_condition(file: str, line: int, column: int, snippet: str) -> RynxError:
    return RynxError(
        code="RX206",
        name="InvalidCondition",
        message="Condition must be yes",
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )


def rx207_invalid_break(file: str, line: int, column: int, snippet: str) -> RynxError:
    return RynxError(
        code="RX207",
        name="InvalidBreak",
        message="break only allowed inside loop",
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )


def rx208_redeclaration(file: str, line: int, column: int, snippet: str, name: str) -> RynxError:
    return RynxError(
        code="RX208",
        name="Redeclaration",
        message=f"Redeclaration in same scope: {name}",
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )


def rx209_empty_task_body(file: str, line: int, column: int, snippet: str, task_name: str) -> RynxError:
    return RynxError(
        code="RX209",
        name="EmptyTaskBody",
        message=f"Task body cannot be empty: {task_name}",
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )


def rx212_show_requires_arg(file: str, line: int, column: int, snippet: str) -> RynxError:
    return RynxError(
        code="RX212",
        name="ShowRequiresArg",
        message="show requires at least one argument",
        file=file,
        line=line,
        column=column,
        snippet=snippet,
    )
