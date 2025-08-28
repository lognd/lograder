from typing import Callable, Generator

from .types import TestCase

def make_tests_from_generator(
        generator: Callable[[], Generator[TestCase, None, None]]
) -> None:
    # TODO: Make the `@make_tests_from_generator` as specified in the README.md
    ...
