from abc import ABC
from typing import TypeVar

from lograder.pipeline.step import Step

InputT = TypeVar("InputT")
OkOutputT = TypeVar("OkOutputT")
ErrOutputT = TypeVar("ErrOutputT")
OkDisplayT = TypeVar("OkDisplayT")
ErrDisplayT = TypeVar("ErrDisplayT")


class Input(Step[InputT, OkOutputT, ErrOutputT, OkDisplayT, ErrDisplayT], ABC): ...
