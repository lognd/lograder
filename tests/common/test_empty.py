# type: ignore

from __future__ import annotations

import pytest

from lograder.common import Empty, Singleton, Unreachable


class MyEmpty(Empty):
    pass


class MySingleton(Singleton):
    pass


class MyOtherSingleton(Singleton):
    pass


def test_empty_is_instantiable() -> None:
    obj = Empty()
    assert isinstance(obj, Empty)


def test_empty_has_no_instance_dict() -> None:
    obj = Empty()
    assert not hasattr(obj, "__dict__")


def test_empty_subclass_has_no_instance_dict_by_default() -> None:
    obj = MyEmpty()
    assert not hasattr(obj, "__dict__")


def test_singleton_subclass_is_instance_of_singleton() -> None:
    obj = MySingleton()
    assert isinstance(obj, Singleton)
    assert isinstance(obj, MySingleton)


def test_singleton_returns_same_instance_for_same_subclass() -> None:
    a = MySingleton()
    b = MySingleton()
    assert a is b


def test_distinct_singleton_subclasses_produce_distinct_instances() -> None:
    a = MySingleton()
    b = MyOtherSingleton()
    assert type(a) is MySingleton
    assert type(b) is MyOtherSingleton
    assert a is not b


def test_unreachable_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError) as excinfo:
        Unreachable()

    msg = str(excinfo.value)
    assert "`UNREACHABLE` was instantiated at " in msg
    assert "This sentinel should never be constructed at runtime." in msg


def test_unreachable_error_contains_callsite_function_name() -> None:
    def trigger() -> None:
        Unreachable()

    with pytest.raises(TypeError) as excinfo:
        trigger()

    assert "in trigger()" in str(excinfo.value)
