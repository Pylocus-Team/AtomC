"""
Rynx 2.0 Parser State — Token stream with current position.
No magic. Explicit peek/advance. First error only.
"""

from typing import List, Optional

from atomc.compiler.lexer.token import Token, TokenKind


class ParserState:
    """Mutable state: list of tokens and current index. Optional source for snippet in errors."""

    def __init__(self, tokens: List[Token], filename: str = "main.ryx", source: Optional[str] = None) -> None:
        self.tokens = tokens
        self.filename = filename
        self.source = source
        self.index = 0

    def at_end(self) -> bool:
        return self.index >= len(self.tokens) or self.current().kind == TokenKind.EOF

    def current(self) -> Token:
        if self.index >= len(self.tokens):
            return self.tokens[-1] if self.tokens else Token(TokenKind.EOF, line=1, column=1, end_column=1)
        return self.tokens[self.index]

    def peek(self, offset: int = 0) -> Token:
        pos = self.index + offset
        if pos >= len(self.tokens):
            return self.tokens[-1] if self.tokens else Token(TokenKind.EOF, line=1, column=1, end_column=1)
        return self.tokens[pos]

    def advance(self) -> Token:
        if self.index >= len(self.tokens):
            return self.tokens[-1] if self.tokens else Token(TokenKind.EOF, line=1, column=1, end_column=1)
        t = self.tokens[self.index]
        self.index += 1
        return t

    def expect(self, kind: TokenKind) -> Token:
        t = self.current()
        if t.kind != kind:
            raise self._unexpected(t, kind)
        return self.advance()

    def check(self, kind: TokenKind) -> bool:
        return self.current().kind == kind

    def check_any(self, *kinds: TokenKind) -> bool:
        return self.current().kind in kinds

    def _unexpected(self, t: Token, expected: TokenKind):
        from atomc.compiler.parser.parser_errors import rx102_unexpected_token
        from atomc.errors.snippets import get_line_snippet
        if self.source:
            snippet = get_line_snippet(self.source, t.line)
        else:
            snippet = str(t.value) if t.value is not None else (t.kind.value or "")
            if len(snippet) > 80:
                snippet = snippet[:77] + "..."
        got = str(t.kind.value) if t.kind != TokenKind.EOF else "eof"
        return rx102_unexpected_token(self.filename, t.line, t.column, snippet, got)
