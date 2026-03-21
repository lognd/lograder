from abc import ABC
from typing import TypeVar

from pydantic import BaseModel

from ..step import Step


class CheckError(BaseModel):
    check_name: str


class CheckData(BaseModel):
    check_name: str


InputT = TypeVar("InputT")
OkOutputT = TypeVar("OkOutputT")
ErrOutputT = TypeVar("ErrOutputT")
OkDisplayT = TypeVar("OkDisplayT")
ErrDisplayT = TypeVar("ErrDisplayT")


class Check(Step[InputT, OkOutputT, ErrOutputT, OkDisplayT, ErrDisplayT], ABC): ...
