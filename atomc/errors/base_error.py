"""
Rynx 2.0 Error System — Base Error Structure.
Mandatory structure per specification. No custom messages.
First error only. Deterministic.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RynxError(Exception):
    """
    Mandatory error object. Every compile-time and runtime error
    MUST use this structure. Pixel-perfect output depends on it.
    """
    code: str
    name: str
    message: str
    file: str
    line: int
    column: int
    snippet: str
    # Optional: for type mismatch, expected/found
    expected: Optional[str] = None
    found: Optional[str] = None

    def is_compile_error(self) -> bool:
        """RX1xx, RX2xx, RX3xx → compile-time."""
        if len(self.code) >= 4 and self.code.startswith("RX"):
            try:
                hundred = int(self.code[2])
                return hundred in (1, 2, 3)
            except ValueError:
                pass
        return False

    def is_runtime_error(self) -> bool:
        """RX5xx → runtime."""
        if len(self.code) >= 4 and self.code.startswith("RX"):
            try:
                hundred = int(self.code[2])
                return hundred == 5
            except ValueError:
                pass
        return False
