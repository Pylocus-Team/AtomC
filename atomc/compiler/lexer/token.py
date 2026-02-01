"""
Rynx 2.0 Token — Explicit token structure with line/column.
Every token has: kind, value (optional), line, column, end_column.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class TokenKind(Enum):
    # Keywords
    KW_START = "start"
    KW_END = "end"
    KW_TASK = "task"
    KW_WHEN = "when"
    KW_ELSE = "else"
    KW_LOOP = "loop"
    KW_THRU = "thru"
    KW_EACH = "each"
    KW_IN = "in"
    KW_MATCH = "match"
    KW_CASE = "case"
    KW_FLOW = "flow"
    KW_BREAK = "break"
    KW_RETURN = "return"
    KW_LET = "let"
    KW_GUESS = "guess"
    KW_BLOCK = "block"
    KW_STEP = "step"
    KW_SHOW = "show"
    # Types
    KW_NUM = "num"
    KW_DEC = "dec"
    KW_TEXT = "text"
    KW_YES = "yes"
    KW_NUMS = "nums"
    KW_TEXTS = "texts"
    KW_DECS = "decs"
    KW_YESS = "yess"
    # Literals
    KW_TRUE = "true"
    KW_FALSE = "false"
    # Identifiers and literals
    IDENT = "ident"
    NUM_LIT = "num_lit"
    TEXT_LIT = "text_lit"
    # Operators
    OP_ADD = "+"
    OP_SUB = "-"
    OP_MUL = "*"
    OP_DIV = "/"
    OP_MOD = "%"
    OP_LT = "<"
    OP_GT = ">"
    OP_LE = "<="
    OP_GE = ">="
    OP_EQ = "=="
    OP_NE = "!="
    OP_AND = "&&"
    OP_OR = "||"
    OP_NOT = "!"
    OP_DOTDOT = ".."
    OP_ASSIGN = "="
    # Delimiters
    LBRACE = "{"
    RBRACE = "}"
    LPAREN = "("
    RPAREN = ")"
    LBRACK = "["
    RBRACK = "]"
    COMMA = ","
    SEMI = ";"
    COLON = ":"
    # End of input
    EOF = "eof"


@dataclass
class Token:
    kind: TokenKind
    value: Optional[Any] = None
    line: int = 1
    column: int = 1
    end_column: int = 1

    def __repr__(self) -> str:
        v = f", {self.value!r}" if self.value is not None else ""
        return f"Token({self.kind.name}{v}, L{self.line}:{self.column})"


# Map from keyword string to TokenKind (for lexer)
KEYWORDS: dict[str, TokenKind] = {
    "start": TokenKind.KW_START,
    "end": TokenKind.KW_END,
    "task": TokenKind.KW_TASK,
    "when": TokenKind.KW_WHEN,
    "else": TokenKind.KW_ELSE,
    "loop": TokenKind.KW_LOOP,
    "thru": TokenKind.KW_THRU,
    "each": TokenKind.KW_EACH,
    "in": TokenKind.KW_IN,
    "match": TokenKind.KW_MATCH,
    "case": TokenKind.KW_CASE,
    "flow": TokenKind.KW_FLOW,
    "break": TokenKind.KW_BREAK,
    "return": TokenKind.KW_RETURN,
    "let": TokenKind.KW_LET,
    "guess": TokenKind.KW_GUESS,
    "block": TokenKind.KW_BLOCK,
    "step": TokenKind.KW_STEP,
    "show": TokenKind.KW_SHOW,
    "num": TokenKind.KW_NUM,
    "dec": TokenKind.KW_DEC,
    "text": TokenKind.KW_TEXT,
    "yes": TokenKind.KW_YES,
    "nums": TokenKind.KW_NUMS,
    "texts": TokenKind.KW_TEXTS,
    "decs": TokenKind.KW_DECS,
    "yess": TokenKind.KW_YESS,
    "true": TokenKind.KW_TRUE,
    "false": TokenKind.KW_FALSE,
}
