"""
Rynx 2.0 Compile Pipeline — Lexer → Parser → Semantic Analysis.
No IR. No bytecode. First error only. Exit 2 on compile error.
"""

from typing import Optional

from atomc.compiler.lexer import lex
from atomc.compiler.parser.parser import parse
from atomc.compiler.semantic.analyzer import SemanticAnalyzer
from atomc.ast.ast_nodes import ProgramNode
from atomc.errors.base_error import RynxError
from atomc.errors.error_formatter import format_compile_error
import sys


def compile_source(source: str, filename: str = "main.ryx") -> ProgramNode:
    """
    Lex, parse, and semantically analyze source.
    On first error: print diagnostic, raise RynxError (caller should exit 2).
    """
    tokens = lex(source, filename)
    ast = parse(tokens, filename, source)
    analyzer = SemanticAnalyzer(filename, source)
    analyzer.analyze(ast)
    return ast


def compile_and_run(source: str, filename: str = "main.ryx") -> int:
    """
    Compile and run. Return exit code.
    - Compile error: print, return 2
    - Runtime error: print (in interpreter), return 1
    - Success: return 0 or 1 (from end 0 / end 1)
    """
    try:
        ast = compile_source(source, filename)
    except RynxError as e:
        format_compile_error(e, sys.stderr)
        return 2
    from atomc.runtime.runtime import Interpreter
    interpreter = Interpreter(ast, filename, source)
    return interpreter.run()
