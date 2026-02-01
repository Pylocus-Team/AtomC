"""
Rynx 2.0 Snippets — Extract line snippet from source for diagnostics.
Deterministic. No truncation magic.
"""


def get_line_snippet(source: str, line: int) -> str:
    """
    Return the content of the given 1-based line from source.
    If line is out of range, return empty string.
    """
    lines = source.splitlines()
    if line < 1 or line > len(lines):
        return ""
    return lines[line - 1]


def get_line_at_position(source: str, position: int) -> int:
    """
    Return 1-based line number for the given 0-based character position.
    """
    if position < 0:
        return 1
    lines = source.splitlines(keepends=True)
    current = 0
    for i, part in enumerate(lines):
        current += len(part)
        if position < current:
            return i + 1
    return len(lines) if lines else 1


def get_column_at_position(source: str, position: int) -> int:
    """
    Return 1-based column number for the given 0-based character position.
    """
    if position < 0:
        return 1
    before = source[:position]
    last_newline = before.rfind("\n")
    if last_newline == -1:
        return position + 1
    return position - last_newline
