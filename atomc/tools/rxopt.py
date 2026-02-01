#!/usr/bin/env python3
"""
rxopt — Rynx optimizer. object (.ro) → optimized object (.ro).
Usage: rxopt main.ro -O2 -o main.opt.ro
Optimizes AST/IR without changing program meaning.
"""

import sys
import os
import argparse

from atomc.object.format import read_ro, write_ro


def main() -> int:
    parser = argparse.ArgumentParser(prog="rxopt", description="Rynx optimizer: .ro → .ro")
    parser.add_argument("input", help="Input .ro object file")
    parser.add_argument("-o", "--output", required=True, help="Output .ro object file")
    parser.add_argument("-O", "--opt-level", type=int, default=0, choices=[0, 1, 2],
                        help="Optimization level (0=none, 1=basic, 2=full)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"rxopt: file not found: {args.input}", file=sys.stderr)
        return 2

    try:
        payload = read_ro(args.input)
    except Exception as e:
        print(f"rxopt: invalid object file: {e}", file=sys.stderr)
        return 2

    ast = payload["ast"]
    source = payload.get("source")
    filename = payload.get("filename", "main.ryx")

    # Optimization pass: no-op for now (AST unchanged; future: constant fold, dead code, etc.)
    if args.opt_level >= 1:
        pass
    if args.opt_level >= 2:
        pass

    try:
        write_ro(ast, args.output, source=source, filename=filename)
        return 0
    except OSError as e:
        print(f"rxopt: cannot write {args.output}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
