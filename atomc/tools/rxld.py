#!/usr/bin/env python3
"""
rxld — Rynx linker. object(s) (.ro) → executable (.rxe).
Usage: rxld main.opt.ro -o app.rxe
Links one or more object files into a single executable.
"""

import sys
import os
import argparse

from atomc.object.format import read_ro, write_rxe


def main() -> int:
    parser = argparse.ArgumentParser(prog="rxld", description="Rynx linker: .ro → .rxe")
    parser.add_argument("inputs", nargs="+", help="Input .ro object file(s)")
    parser.add_argument("-o", "--output", required=True, help="Output .rxe executable file")
    args = parser.parse_args()

    if not args.inputs:
        print("rxld: no input files", file=sys.stderr)
        return 2

    # For now: single entry object; first file is the main program.
    main_path = args.inputs[0]
    if not os.path.isfile(main_path):
        print(f"rxld: file not found: {main_path}", file=sys.stderr)
        return 2

    try:
        payload = read_ro(main_path)
    except Exception as e:
        print(f"rxld: invalid object file: {e}", file=sys.stderr)
        return 2

    ast = payload["ast"]
    source = payload.get("source")
    filename = payload.get("filename", "main.ryx")

    # Future: merge multiple .ro (modules) into one program.
    for p in args.inputs[1:]:
        if not os.path.isfile(p):
            print(f"rxld: file not found: {p}", file=sys.stderr)
            return 2
        # Could read and merge ASTs here.

    try:
        write_rxe(ast, args.output, source=source, filename=filename)
        return 0
    except OSError as e:
        print(f"rxld: cannot write {args.output}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
