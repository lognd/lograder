from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Mapping, Type

from pydantic import BaseModel

from ...types import FormatLabel

if TYPE_CHECKING:
    from .formatter import FormatterInterface


class FormatPackage(BaseModel):
    label: FormatLabel
    data: Mapping[str, Any]


def register_format(label: FormatLabel):
    def decorator(cls: Type[FormatterInterface]):
        FormatDispatcher.register(label, cls)
        setattr(cls, "__registered_format__", label)
        return cls

    return decorator


class FormatDispatcher:
    _registered_formats: Dict[FormatLabel, Type[FormatterInterface]] = {}

    @classmethod
    def register(cls, label: FormatLabel, formatter: Type[FormatterInterface]) -> None:
        cls._registered_formats[label] = formatter

    @classmethod
    def get(cls, label: FormatLabel) -> Type[FormatterInterface]:
        return cls._registered_formats[label]

    @classmethod
    def format(cls, package: FormatPackage) -> str:
        label = package.label
        data = package.data
        return cls.get(label).to_string(data)
