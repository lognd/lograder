# type: ignore

from __future__ import annotations

import pytest

from lograder.common import Err, Ok, Result
from lograder.exception import DeveloperException


def test_ok_constructor_sets_ok_state() -> None:
    r = Ok(123)

    assert isinstance(r, Result)
    assert r.is_ok is True
    assert r.is_err is False
    assert r.ok == 123
    assert r.err is None
    assert r.danger_ok == 123


def test_err_constructor_sets_err_state() -> None:
    r = Err("boom")

    assert isinstance(r, Result)
    assert r.is_ok is False
    assert r.is_err is True
    assert r.ok is None
    assert r.err == "boom"
    assert r.danger_err == "boom"


def test_result_rejects_neither_ok_nor_err() -> None:
    with pytest.raises(DeveloperException) as excinfo:
        Result()

    assert "neither an `ok` option specified or an `err` option specified" in str(
        excinfo.value
    )


def test_result_rejects_both_ok_and_err() -> None:
    with pytest.raises(DeveloperException) as excinfo:
        Result(ok=1, err="bad")

    msg = str(excinfo.value)
    assert "both an `ok` option" in msg
    assert "and an `err` option" in msg


def test_ok_allows_none_as_legitimate_ok_value() -> None:
    r = Ok(None)

    assert r.is_ok is True
    assert r.is_err is False
    assert r.ok is None
    assert r.danger_ok is None


def test_err_allows_none_as_legitimate_err_value() -> None:
    r = Err(None)

    assert r.is_ok is False
    assert r.is_err is True
    assert r.err is None
    assert r.danger_err is None


def test_map_transforms_ok_value() -> None:
    r = Ok(5).map(lambda x: x * 2)

    assert r.is_ok
    assert r.ok == 10


def test_map_does_not_transform_err_value() -> None:
    called = False

    def func(x: int) -> int:
        nonlocal called
        called = True
        return x * 2

    r = Err("bad").map(func)

    assert r.is_err
    assert r.err == "bad"
    assert called is False


def test_map_returns_same_object_for_err() -> None:
    r = Err("bad")
    mapped = r.map(lambda x: x)

    assert mapped is r


def test_map_err_transforms_err_value() -> None:
    r = Err("bad").map_err(str.upper)

    assert r.is_err
    assert r.err == "BAD"


def test_map_err_does_not_transform_ok_value() -> None:
    called = False

    def func(e: str) -> str:
        nonlocal called
        called = True
        return e.upper()

    r = Ok(123).map_err(func)

    assert r.is_ok
    assert r.ok == 123
    assert called is False


def test_map_err_returns_same_object_for_ok() -> None:
    r = Ok(10)
    mapped = r.map_err(lambda e: e)

    assert mapped is r


def test_and_then_on_ok_with_ok_result() -> None:
    r = Ok(5).and_then(lambda x: Ok(x + 1))

    assert r.is_ok
    assert r.ok == 6


def test_and_then_on_ok_with_err_result() -> None:
    r = Ok(5).and_then(lambda x: Err(f"bad:{x}"))

    assert r.is_err
    assert r.err == "bad:5"


def test_and_then_on_err_short_circuits() -> None:
    called = False

    def func(x: int):
        nonlocal called
        called = True
        return Ok(x + 1)

    r = Err("boom").and_then(func)

    assert r.is_err
    assert r.err == "boom"
    assert called is False


def test_or_else_on_err_with_ok_result() -> None:
    r = Err("boom").or_else(lambda e: Ok(len(e)))

    assert r.is_ok
    assert r.ok == 4


def test_or_else_on_err_with_err_result() -> None:
    r = Err("boom").or_else(lambda e: Err(e.upper()))

    assert r.is_err
    assert r.err == "BOOM"


def test_or_else_on_ok_short_circuits() -> None:
    called = False

    def func(e: str):
        nonlocal called
        called = True
        return Ok(0)

    r = Ok(42).or_else(func)

    assert r.is_ok
    assert r.ok == 42
    assert called is False


def test_inspect_calls_function_for_ok_and_returns_self() -> None:
    seen = []

    r = Ok(123)
    out = r.inspect(lambda x: seen.append(x))

    assert out is r
    assert seen == [123]


def test_inspect_does_not_call_function_for_err_and_returns_self() -> None:
    seen = []

    r = Err("bad")
    out = r.inspect(lambda x: seen.append(x))

    assert out is r
    assert seen == []


def test_danger_ok_asserts_on_err() -> None:
    r = Err("boom")
    with pytest.raises(AssertionError):
        _ = r.danger_ok


def test_danger_err_asserts_on_ok() -> None:
    r = Ok(1)
    with pytest.raises(AssertionError):
        _ = r.danger_err


def test_chained_map_and_then_and_map_err_ok_path() -> None:
    r = (
        Ok(3)
        .map(lambda x: x + 1)
        .and_then(lambda x: Ok(x * 10))
        .map_err(lambda e: f"ERR:{e}")
    )

    assert r.is_ok
    assert r.ok == 40


def test_chained_map_and_then_and_map_err_err_path() -> None:
    r = (
        Ok(3)
        .map(lambda x: x + 1)
        .and_then(lambda x: Err(f"bad:{x}"))
        .map_err(lambda e: f"ERR:{e}")
    )

    assert r.is_err
    assert r.err == "ERR:bad:4"
