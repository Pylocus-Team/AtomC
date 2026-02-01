"""
Rynx 2.0 Error Formatter — Pixel-Perfect Output.
Output format is LOCKED. Identical across implementations.
"""

from typing import TextIO

from atomc.errors.base_error import RynxError


def format_compile_error(err: RynxError, out: TextIO) -> None:
    """
    Compile-time error output. Exact format per specification.
    [RYNX COMPILE ERROR] RX201: Type mismatch
      File: main.ryx
      Line: 12, Column: 8

      12 | num x = "hi";
         |        ^^^^^^^

    Expected: num
    Found: text
    """
    out.write(f"[RYNX COMPILE ERROR] {err.code}: {err.message}\n")
    out.write(f"  File: {err.file}\n")
    out.write(f"  Line: {err.line}, Column: {err.column}\n")
    out.write("\n")
    out.write(f"  {err.line:>4} | {err.snippet}\n")
    out.write("       | " + " " * _column_offset(err.snippet, err.column) + "^\n")
    if err.expected is not None:
        out.write(f"\nExpected: {err.expected}\n")
    if err.found is not None:
        out.write(f"Found: {err.found}\n")
    out.flush()


def format_runtime_error(err: RynxError, out: TextIO) -> None:
    """
    Runtime error output. Graceful. Then program terminates with end 1.
    """
    out.write(f"[RYNX RUNTIME ERROR] {err.code}: {err.message}\n")
    out.write(f"  File: {err.file}\n")
    out.write(f"  Line: {err.line}, Column: {err.column}\n")
    out.write("\n")
    out.write(f"  {err.line:>4} | {err.snippet}\n")
    out.write("       | " + " " * _column_offset(err.snippet, err.column) + "^\n")
    if err.expected is not None:
        out.write(f"\n{err.expected}\n")
    out.write("\nProgram terminated (end 1)\n")
    out.flush()


def _column_offset(snippet: str, column: int) -> int:
    """Number of spaces so that ^ aligns with column (1-based) in snippet."""
    if column <= 0:
        return 0
    return min(column - 1, len(snippet))
