#!/usr/bin/env python3
"""
rxc — Rynx compiler. source (.ryx) → object (.ro).
Usage: rxc src/main.ryx -o main.ro
"""

import sys
import os
import argparse

from atomc.errors.base_error import RynxError
from atomc.errors.error_formatter import format_compile_error
from atomc.compiler.lexer import lex
from atomc.compiler.parser.parser import parse
from atomc.compiler.semantic.analyzer import SemanticAnalyzer
from atomc.object.format import write_ro


def main() -> int:
    parser = argparse.ArgumentParser(prog="rxc", description="Rynx compiler: .ryx → .ro")
    parser.add_argument("source", help="Input .ryx source file")
    parser.add_argument("-o", "--output", required=True, help="Output .ro object file")
    args = parser.parse_args()

    path = args.source
    if not os.path.isfile(path):
        print(f"rxc: file not found: {path}", file=sys.stderr)
        return 2
    filename = os.path.basename(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        print(f"rxc: cannot read {path}: {e}", file=sys.stderr)
        return 2

    try:
        tokens = lex(source, filename)
        ast = parse(tokens, filename, source)
        analyzer = SemanticAnalyzer(filename, source)
        analyzer.analyze(ast)
        write_ro(ast, args.output, source=source, filename=filename)
        return 0
    except RynxError as e:
        format_compile_error(e, sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
