"""
Rynx object format — .ro (object) and .rxe (executable).
Serializes validated AST + metadata. No bytecode.
"""

import pickle
from pathlib import Path
from typing import Any, Dict, Optional

from atomc.ast.ast_nodes import ProgramNode

OBJECT_VERSION = 1
RXE_MAGIC = b"RYNX-RXE-1\n"


def write_ro(ast: ProgramNode, path: str, source: Optional[str] = None, filename: str = "main.ryx") -> None:
    """
    Write Rynx object file (.ro).
    Contains: version, AST, optional source and filename for diagnostics.
    """
    payload: Dict[str, Any] = {
        "version": OBJECT_VERSION,
        "ast": ast,
        "source": source,
        "filename": filename,
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)


def read_ro(path: str) -> Dict[str, Any]:
    """Read Rynx object file (.ro). Returns dict with ast, source?, filename?."""
    with open(path, "rb") as f:
        payload = pickle.load(f)
    if not isinstance(payload, dict) or "ast" not in payload:
        raise ValueError(f"Invalid .ro file: {path}")
    return payload


def write_rxe(ast: ProgramNode, path: str, source: Optional[str] = None, filename: str = "main.ryx") -> None:
    """
    Write Rynx executable (.rxe).
    Same as .ro with magic header for identification.
    """
    payload: Dict[str, Any] = {
        "version": OBJECT_VERSION,
        "ast": ast,
        "source": source,
        "filename": filename,
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(RXE_MAGIC)
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)


def read_rxe(path: str) -> Dict[str, Any]:
    """Read Rynx executable (.rxe)."""
    with open(path, "rb") as f:
        magic = f.read(len(RXE_MAGIC))
        if magic != RXE_MAGIC:
            raise ValueError(f"Invalid .rxe file (bad magic): {path}")
        payload = pickle.load(f)
    if not isinstance(payload, dict) or "ast" not in payload:
        raise ValueError(f"Invalid .rxe file: {path}")
    return payload
