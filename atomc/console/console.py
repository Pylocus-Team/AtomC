#!/usr/bin/env python3
"""
AtomC Developer Console — TUI orchestrator for rxc, rxopt, rxld, rxrun.
Strict mode: manages 'build/' and 'bin/' folders automatically.
Rewrites paths to force standard project structure.
"""

import sys
import os
import subprocess
import shlex
import argparse
from pathlib import Path

# Resolve tools as Python modules (same repo)
CONSOLE_VERSION = "0.2 (Strict)"
TOOL_MODULES = {
    "rxc": "atomc.tools.rxc",
    "rxopt": "atomc.tools.rxopt",
    "rxld": "atomc.tools.rxld",
    "rxrun": "atomc.tools.rxrun",
}

def ensure_dirs():
    """Ensure build/ and bin/ directories exist."""
    os.makedirs("build", exist_ok=True)
    os.makedirs("bin", exist_ok=True)

def print_error(code: str, msg: str):
    print(f"[RYNX CONSOLE ERROR] {code}: {msg}")

def process_rxc(args: list) -> tuple[int, list]:
    """
    Rewrite: rxc <src> -o <out.ro>
    -> rxc <src> -o build/<out.ro>
    Check: <src> exists (RX201)
    """
    # Simple manual parse to find source and -o
    input_file = None
    output_file = None
    
    # Heuristic: First arg without startsWith('-') is input
    # -o <val> is output
    
    new_args = []
    skip_next = False
    
    for i, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue
            
        if arg == "-o":
            if i + 1 < len(args):
                val = args[i+1]
                # Strip any directory user might have tried to add
                output_file = Path(val).name 
                new_args.append("-o")
                new_args.append(str(Path("build") / output_file))
                skip_next = True
            else:
                new_args.append(arg)
        elif not arg.startswith("-") and input_file is None:
            input_file = arg
            new_args.append(arg)
        else:
            new_args.append(arg)
            
    if not input_file:
        # Let the tool handle help/error if no input
        return 0, args
        
    if not os.path.isfile(input_file):
        print_error("RX201", f"Source file not found: {input_file}")
        return 2, []
        
    if not output_file:
        # If user didn't specify -o, we should technically error or default
        # But for now let's pass it through or add default?
        # Specification says user MUST specify strict syntax.
        # Let's assume standard usage for now.
        pass
        
    return 0, new_args

def process_rxopt(args: list) -> tuple[int, list]:
    """
    Rewrite: rxopt <in.ro> ... -o <out.opt.ro>
    -> rxopt build/<in.ro> ... -o build/<out.opt.ro>
    Check: build/<in.ro> exists (RX210)
    """
    input_file = None
    output_file = None
    new_args = []
    skip_next = False
    
    for i, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue
            
        if arg == "-o":
            if i + 1 < len(args):
                val = args[i+1]
                output_file = Path(val).name
                new_args.append("-o")
                new_args.append(str(Path("build") / output_file))
                skip_next = True
            else:
                new_args.append(arg)
        elif not arg.startswith("-") and input_file is None:
            # Input file is expected to be just the name, console maps to build/
            val = Path(arg).name
            input_file = str(Path("build") / val)
            new_args.append(input_file)
        else:
            new_args.append(arg)

    if input_file:
        if not os.path.isfile(input_file):
            print_error("RX210", f"Object file not found: {input_file}")
            return 2, []

    return 0, new_args

def process_rxld(args: list) -> tuple[int, list]:
    """
    Rewrite: rxld <in.opt.ro> ... -o <out.rxe>
    -> rxld build/<in.opt.ro> ... -o bin/<out.rxe>
    Check: build/<in.opt.ro> exists (RX220)
    """
    input_file = None
    output_file = None
    new_args = []
    skip_next = False
    
    for i, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue
            
        if arg == "-o":
            if i + 1 < len(args):
                val = args[i+1]
                output_file = Path(val).name
                new_args.append("-o")
                new_args.append(str(Path("bin") / output_file))
                skip_next = True
            else:
                new_args.append(arg)
        elif not arg.startswith("-") and input_file is None:
            val = Path(arg).name
            input_file = str(Path("build") / val)
            new_args.append(input_file)
        else:
            new_args.append(arg)

    if input_file:
        if not os.path.isfile(input_file):
            print_error("RX220", f"Optimized object not found: {input_file}")
            return 2, []

    return 0, new_args

def process_rxrun(args: list) -> tuple[int, list]:
    """
    Rewrite: rxrun <app.rxe>
    -> rxrun bin/<app.rxe>
    Check: bin/<app.rxe> exists (RX301)
    """
    input_file = None
    new_args = []
    
    for arg in args:
        if not arg.startswith("-") and input_file is None:
            val = Path(arg).name
            input_file = str(Path("bin") / val)
            new_args.append(input_file)
        else:
            new_args.append(arg)
            
    if input_file:
        if not os.path.isfile(input_file):
            print_error("RX301", f"Executable not found: {input_file}")
            return 2, []
            
    return 0, new_args

def run_tool(name: str, args: list) -> int:
    """Run tool as Python module. Returns exit code."""
    ensure_dirs()
    
    # Pre-process args based on command policies
    exit_code = 0
    final_args = args
    
    if name == "rxc":
        exit_code, final_args = process_rxc(args)
    elif name == "rxopt":
        exit_code, final_args = process_rxopt(args)
    elif name == "rxld":
        exit_code, final_args = process_rxld(args)
    elif name == "rxrun":
        exit_code, final_args = process_rxrun(args)
        
    if exit_code != 0:
        return exit_code
        
    module = TOOL_MODULES.get(name)
    if not module:
        return -1
        
    cmd = [sys.executable, "-m", module] + final_args
    # Debug print to show user what's happening under hood
    # print(f"[DEBUG] Executing: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except FileNotFoundError:
        print(f"atomc: could not run Python: {sys.executable}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"atomc: {name} failed: {e}", file=sys.stderr)
        return 2


def parse_line(line: str) -> tuple:
    """Parse command line into (command, args). Handles simple quoting."""
    line = line.strip()
    if not line:
        return "", []
    parts = shlex.split(line, posix=(os.name != "nt"))
    if not parts:
        return "", []
    cmd = parts[0].lower()
    return cmd, parts[1:]


def main() -> int:
    print("AtomC Developer Console " + CONSOLE_VERSION)
    print()
    print("Managed folders: build/ (objects), bin/ (executables)")
    print("Example Workflow:")
    print("  1. rxc src/main.ryx -o main.ro")
    print("  2. rxopt main.ro -O2 -o main.opt.ro")
    print("  3. rxld main.opt.ro -o app.rxe")
    print("  4. rxrun app.rxe")
    print()
    
    ensure_dirs()

    while True:
        try:
            line = input("> ")
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            continue

        cmd_name, args = parse_line(line)
        if not cmd_name:
            continue
        if cmd_name == "exit":
            break
        if cmd_name == "help":
            print("Commands are rewritten to use build/ and bin/ automatically.")
            print("rxc <source.ryx> -o <output.ro>")
            print("rxopt <input.ro> -o <output.ro> [-O2]")
            print("rxld <input.ro> [...] -o <app.rxe>")
            print("rxrun <app.rxe>")
            print("exit")
            continue

        if cmd_name not in TOOL_MODULES:
            print(f"Unknown command: {cmd_name}. Use: rxc, rxopt, rxld, rxrun, help, exit")
            continue

        run_tool(cmd_name, args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
