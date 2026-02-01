"""
Rynx 2.0 Type System — Static, closed. No implicit conversions.
Primitive types: num, dec, text, yes. List types: nums, texts, decs, yess.
"""

from atomc.ast.ast_nodes import TypeKind, Expr
from typing import Optional, Tuple


def type_kind_to_str(k: TypeKind) -> str:
    return k.value


def is_numeric(t: TypeKind) -> bool:
    return t in (TypeKind.NUM, TypeKind.DEC)


def is_list_type(t: TypeKind) -> bool:
    return t in (TypeKind.NUMS, TypeKind.TEXTS, TypeKind.DECS, TypeKind.YESS)


def element_type(list_t: TypeKind) -> Optional[TypeKind]:
    if list_t == TypeKind.NUMS:
        return TypeKind.NUM
    if list_t == TypeKind.TEXTS:
        return TypeKind.TEXT
    if list_t == TypeKind.DECS:
        return TypeKind.DEC
    if list_t == TypeKind.YESS:
        return TypeKind.YES
    return None


def comparable(left: TypeKind, right: TypeKind) -> bool:
    """Comparison operators: same type or both numeric."""
    if left == right:
        return True
    if is_numeric(left) and is_numeric(right):
        return True
    return False


def arithmetic_result(left: TypeKind, right: TypeKind) -> Optional[TypeKind]:
    """+ - * / %: both num -> num; both dec -> dec; mixed -> dec."""
    if left == TypeKind.NUM and right == TypeKind.NUM:
        return TypeKind.NUM
    if left == TypeKind.DEC or right == TypeKind.DEC:
        return TypeKind.DEC
    return None


def concat_result(left: TypeKind, right: TypeKind) -> Optional[TypeKind]:
    """text + text -> text."""
    if left == TypeKind.TEXT and right == TypeKind.TEXT:
        return TypeKind.TEXT
    return None


def logic_operand(t: TypeKind) -> bool:
    """&& || ! require yes."""
    return t == TypeKind.YES


def condition_type(t: TypeKind) -> bool:
    """when/flow condition must be yes."""
    return t == TypeKind.YES
