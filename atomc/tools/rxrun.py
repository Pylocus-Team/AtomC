#!/usr/bin/env python3
"""
rxrun — Rynx runtime / VM. Executes .rxe executable.
Usage: rxrun app.rxe
"""

import sys
import os
import argparse

from atomc.object.format import read_rxe
from atomc.runtime.runtime import Interpreter


def main() -> int:
    parser = argparse.ArgumentParser(prog="rxrun", description="Rynx runtime: execute .rxe")
    parser.add_argument("executable", help="Input .rxe executable file")
    args = parser.parse_args()

    if not os.path.isfile(args.executable):
        print(f"rxrun: file not found: {args.executable}", file=sys.stderr)
        return 2

    try:
        payload = read_rxe(args.executable)
    except Exception as e:
        print(f"rxrun: invalid executable: {e}", file=sys.stderr)
        return 2

    ast = payload["ast"]
    source = payload.get("source")
    filename = payload.get("filename", "main.ryx")

    interpreter = Interpreter(ast, filename, source)
    return interpreter.run()


if __name__ == "__main__":
    sys.exit(main())
