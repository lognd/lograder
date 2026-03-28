import re
from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    Generic,
    Literal,
    Optional,
    TypeVar,
    cast,
)

from ansi2html import Ansi2HTMLConverter
from pydantic import BaseModel, Field

from lograder.common import get_bound_types
from lograder.exception import DeveloperException
from lograder.output.packets import PacketAuthority, PacketId

_ANSI_ESCAPE_RE = re.compile(
    r"""
    \x1B  # ESC
    (?:   # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |     # or CSI
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    )
    """,
    re.VERBOSE,
)
_ANSI2HTML = Ansi2HTMLConverter(inline=True)

T = TypeVar("T", bound=BaseModel)


SupportedFormat = Literal["ansi", "ascii", "html", "simple"]


class Layout(ABC, Generic[T]):
    _css_class: str = "layout-all"
    bound_type: Optional[type[T]] = None

    def __init__(self, data: T, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.data = data

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        generic_bound_types = get_bound_types(cls, Layout)
        generic_bound_type = generic_bound_types[0] if generic_bound_types else None

        cls.bound_type = (
            getattr(cls, "__meta_bound_type__", None) or generic_bound_type
        )  # used by dynamic.

    @staticmethod
    def strip_ansi(text: str) -> str:
        return _ANSI_ESCAPE_RE.sub("", text)

    @classmethod
    @abstractmethod
    def to_ansi(cls, data: T) -> str: ...

    @property
    def ansi(self) -> str:
        return self.to_ansi(self.data)

    @classmethod
    @abstractmethod
    def to_simple(cls, data: T) -> str: ...

    @property
    def simple(self) -> str:
        return self.to_simple(self.data)

    @classmethod
    def to_html(cls, data: T) -> str:
        if cls.bound_type is None:
            raise DeveloperException(
                f"`Layout` subclass (`{cls.__name__}`) must specify generic type, i.e. `Layout[Stream]` rather that merely `Layout`."
            )

        return f'<pre class="{cls._css_class} {Layout._css_class}">{_ANSI2HTML.convert(cls.to_ansi(data), full=False)}</pre>'

    @property
    def html(self) -> str:
        return self.to_html(self.data)

    @classmethod
    def to_ascii(cls, data: T) -> str:
        return cls.strip_ansi(cls.to_ansi(data))

    @property
    def ascii(self) -> str:
        return self.to_ascii(self.data)


class LayoutLike(BaseModel):
    to_ansi: Callable[[type[Layout], Any], str]
    to_simple: Callable[[type[Layout], Any], str]
    to_html: Optional[Callable[[type[Layout], Any], str]] = Field(default=None)
    to_ascii: Optional[Callable[[type[Layout], Any], str]] = Field(default=None)


def register_layout(packet_id: str) -> Callable[[type[Layout]], type[Layout]]:
    def wrapper(cls: type[Layout]) -> type[Layout]:
        if cls.bound_type is None:
            raise DeveloperException(
                f"`Layout` subclass (`{cls.__name__}`) must specify generic type, i.e. `Layout[Stream]` rather that merely `Layout`."
            )
        PacketAuthority.register(PacketId(packet_id), cls)
        cls._css_class = f"{packet_id.lower().replace(' ', '-')}-layout"
        return cls

    return wrapper


def dispatch_layout(data: BaseModel) -> Layout:
    packet_id: PacketId = PacketAuthority.access_packet_id(data.__class__)
    layout_cls: type[Layout] = PacketAuthority.access_layout(packet_id)
    return layout_cls(data)
