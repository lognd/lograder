from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Generator, List, Sequence

if TYPE_CHECKING:
    from ..test.interface import TestInterface


class TestRegistry:

    _registry: Dict[str, TestInterface] = {}
    _container: List[TestInterface] = []

    @classmethod
    def clear(cls):
        cls._registry = {}
        cls._container = []

    @classmethod
    def register(cls, key: str, value: TestInterface) -> None:
        cls._registry[key] = value

    @classmethod
    def deregister(cls, key: str) -> None:
        del cls._registry[key]

    @classmethod
    def get(cls, key: str) -> TestInterface:
        return cls._registry[key]

    @classmethod
    def add(cls, value: TestInterface) -> None:
        cls._container.append(value)

    @classmethod
    def extend(cls, values: Sequence[TestInterface]) -> None:
        cls._container.extend(values)

    @classmethod
    def remove(cls, value: TestInterface) -> None:
        cls._container.remove(value)

    @classmethod
    def iterate(cls) -> Generator[TestInterface, None, None]:
        yield from cls._container
