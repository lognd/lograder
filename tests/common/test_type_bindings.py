# type: ignore

from __future__ import annotations

from typing import Generic, TypeVar, Union

import pytest

from lograder.common import (
    get_bound_types,
    get_first_bound_type,
    unwrap_union_types,
)

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


class Box(Generic[T]):
    pass


class Pair(Generic[T, U]):
    pass


class StringBox(Box[str]):
    pass


class IntPair(Pair[int, str]):
    pass


class MidBox(Box[T], Generic[T]):
    pass


class FinalBox(MidBox[int]):
    pass


class Base2(Generic[T, U]):
    pass


class Mid2(Base2[T, str], Generic[T]):
    pass


class Final2(Mid2[int]):
    pass


class Plain:
    pass


class RawBase:
    pass


class ParamBase(Generic[T]):
    pass


class Mixed(RawBase, ParamBase[int]):
    pass


def test_get_first_bound_type_returns_first_type_argument() -> None:
    assert get_first_bound_type(StringBox) is str


def test_get_first_bound_type_returns_none_when_no_orig_bases() -> None:
    assert get_first_bound_type(Plain) is None


def test_get_first_bound_type_with_multiple_bound_types_returns_first_only() -> None:
    assert get_first_bound_type(IntPair) is int


def test_get_bound_types_direct_binding_single_param() -> None:
    assert get_bound_types(StringBox, Box) == (str,)


def test_get_bound_types_direct_binding_multiple_params() -> None:
    assert get_bound_types(IntPair, Pair) == (int, str)


def test_get_bound_types_recursive_binding_through_intermediate_generic() -> None:
    assert get_bound_types(FinalBox, Box) == (int,)


def test_get_bound_types_recursive_binding_with_partial_substitution() -> None:
    assert get_bound_types(Final2, Base2) == (int, str)


def test_get_bound_types_returns_none_for_unrelated_target() -> None:
    assert get_bound_types(StringBox, Pair) is None


def test_get_bound_types_returns_none_when_class_has_no_generic_bases() -> None:
    assert get_bound_types(Plain, Box) is None


def test_get_bound_types_when_target_is_immediate_parent() -> None:
    assert get_bound_types(FinalBox, MidBox) == (int,)


def test_unwrap_union_types_on_typing_union() -> None:
    assert unwrap_union_types(Union[int, str]) == {int, str}


def test_unwrap_union_types_on_non_union_type() -> None:
    assert unwrap_union_types(int) == {int}


def test_unwrap_union_types_on_pep604_union() -> None:
    assert unwrap_union_types(int | str) == {int, str}


def test_unwrap_union_types_on_nested_union() -> None:
    assert unwrap_union_types((int | str) | float) == {int, str, float}


def test_get_first_bound_type_skips_non_parameterized_base_and_finds_next() -> None:
    assert get_first_bound_type(Mixed) is int
