from __future__ import annotations

from typing import Callable, Final, Generic, Optional, TypeVar, cast

from ..exception import DeveloperException
from .empty import Empty

T = TypeVar("T")
V = TypeVar("V")
E = TypeVar("E")
F = TypeVar("F")


# noinspection PyPep8Naming
class _EMPTY_OK(Empty): ...


# noinspection PyPep8Naming
class _EMPTY_ERR(Empty): ...


# Stripped-down version of Rust's `Result<T, E>` macro; I figured this would be helpful.
class Result(Generic[T, E]):
    _OK_SINGLETON: Final[_EMPTY_OK] = _EMPTY_OK()
    _ERR_SINGLETON: Final[_EMPTY_ERR] = _EMPTY_ERR()

    def __init__(
        self, *, ok: T | _EMPTY_OK = _OK_SINGLETON, err: E | _EMPTY_ERR = _ERR_SINGLETON
    ) -> None:
        self._ok: Final[T | _EMPTY_OK] = ok
        self._err: Final[E | _EMPTY_ERR] = err
        if self._ok is Result._OK_SINGLETON and self._err is Result._ERR_SINGLETON:
            raise DeveloperException(
                "There is a `Result` with neither an `ok` option specified or an `err` option specified."
            )
        elif (
            self._ok is not Result._OK_SINGLETON
            and self._err is not Result._ERR_SINGLETON
        ):
            raise DeveloperException(
                f"There is a `Result` with both an `ok` option (type: `{self._ok.__class__.__name__}`, repr: `{self._ok}`) and an `err` option (type: `{self._err.__class__.__name__}`, repr: `{self._err}`) specified."
            )

    def map(self, func: Callable[[T], V]) -> Result[V, E]:
        if self.is_err:
            # cast is safe because invariant is only `err` or `ok` specified.
            # if object `is_err`, then `ok` is empty anyway, and this is safe.
            # noinspection PyUnnecessaryCast
            return cast(Result[V, E], self)
        # cast is safe because `is_err` being false guarantees that `_ok` is valid.
        # noinspection PyUnnecessaryCast
        return Result[V, E](ok=func(cast(T, self._ok)))

    def map_err(self, func: Callable[[E], F]) -> Result[T, F]:
        # casts are safe for the same reasons as above.
        if self.is_ok:
            # noinspection PyUnnecessaryCast
            return cast(Result[T, F], self)
        # noinspection PyUnnecessaryCast
        return Result[T, F](err=func(cast(E, self._err)))

    def and_then(self, func: Callable[[T], Result[V, F]]) -> Result[V, E | F]:
        result = self.map(func)

        # Lots of casting; couple are "unnecessary", but I do it just to appease
        # any checker in the future that's *really* smart (i.e. no double singletons).
        # Additionally, you can check manually but the invariants of `is_err` and
        # `is_ok` ensures each of the following casts are safe.

        if result.is_err:
            # noinspection PyUnnecessaryCast
            return Result[V, E | F](err=cast(E, result._err))
        # noinspection PyUnnecessaryCast
        ok = cast(Result[V, F], result._ok)
        if ok.is_err:
            # noinspection PyUnnecessaryCast
            return Result[V, E | F](err=cast(F, ok._err))
        # noinspection PyUnnecessaryCast
        return Result[V, E | F](ok=cast(V, ok._ok))

    def or_else(self, func: Callable[[E], Result[T, F]]) -> Result[T, F]:
        if self.is_ok:
            # noinspection PyUnnecessaryCast
            return cast(Result[T, F], self)
        # not `is_ok` invariant guarantees `err` cast validity
        # noinspection PyUnnecessaryCast
        return func(cast(E, self.err))

    def inspect(self, func: Callable[[T], None]) -> Result[T, E]:
        if not self.is_err:
            # cast is safe because invariant is only `err` or `ok` specified.
            # if object `is_err`, then `ok` is empty anyway, and this is safe.
            # noinspection PyUnnecessaryCast
            func(cast(T, self._ok))
        return self

    @property
    def is_ok(self) -> bool:
        return self._ok is not Result._OK_SINGLETON

    @property
    def ok(self) -> Optional[T]:
        # cast is safe because `is_ok` guarantees that `_ok` is valid.
        # noinspection PyUnnecessaryCast
        return cast(T, self._ok) if self.is_ok else None

    @property
    def danger_ok(self) -> T:
        assert self.is_ok
        # noinspection PyUnnecessaryCast
        return cast(T, self._ok)

    @property
    def is_err(self) -> bool:
        return self._err is not Result._ERR_SINGLETON

    @property
    def err(self) -> Optional[E]:
        # cast is safe because `is_err` guarantees that `_err` is valid.
        # noinspection PyUnnecessaryCast
        return cast(E, self._err) if self.is_err else None

    @property
    def danger_err(self) -> E:
        assert self.is_err
        # noinspection PyUnnecessaryCast
        return cast(E, self._err)


# noinspection PyPep8Naming
def Ok(ok: T, /) -> Result[T, E]:
    return Result(ok=ok)


# noinspection PyPep8Naming
def Err(err: E, /) -> Result[T, E]:
    return Result(err=err)
