#!/usr/bin/env python3
"""
AtomC / Rynx 2.0 Intercompiler — CLI entry point.
Usage: atomc run <file.ryx>  |  atomc check <file.ryx>
"""

import sys
import os

from atomc.cli.exit_codes import EXIT_SUCCESS, EXIT_RUNTIME_FAIL, EXIT_COMPILE_FAIL
from atomc.errors.base_error import RynxError
from atomc.errors.error_formatter import format_compile_error


def main() -> int:
    argv = sys.argv[1:]
    if not argv:
        print("Usage: atomc run <file.ryx>  |  atomc check <file.ryx>", file=sys.stderr)
        return EXIT_COMPILE_FAIL
    cmd = argv[0].lower()
    if cmd not in ("run", "check"):
        print("Usage: atomc run <file.ryx>  |  atomc check <file.ryx>", file=sys.stderr)
        return EXIT_COMPILE_FAIL
    if len(argv) < 2:
        print("Missing file.ryx", file=sys.stderr)
        return EXIT_COMPILE_FAIL
    path = argv[1]
    if not os.path.isfile(path):
        print(f"File not found: {path}", file=sys.stderr)
        return EXIT_COMPILE_FAIL
    filename = os.path.basename(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        print(f"Cannot read {path}: {e}", file=sys.stderr)
        return EXIT_COMPILE_FAIL
    from atomc.compiler.pipeline import compile_source
    from atomc.runtime.runtime import Interpreter
    try:
        ast = compile_source(source, filename)
    except RynxError as e:
        format_compile_error(e, sys.stderr)
        return EXIT_COMPILE_FAIL
    if cmd == "check":
        return EXIT_SUCCESS
    interpreter = Interpreter(ast, filename, source)
    return interpreter.run()


if __name__ == "__main__":
    sys.exit(main())
