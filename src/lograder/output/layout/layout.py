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

from lograder.common import get_first_bound_type
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
    _packet_id: Optional[str] = None
    bound_type: Optional[type[T]] = None

    def __init__(self, data: T, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.data = data

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.bound_type = getattr(
            cls, "__meta_bound_type__", None
        ) or get_first_bound_type(cls)  # used by dynamic.
        # noinspection PyUnnecessaryCast
        cls._packet_id = PacketAuthority.get_packet_id(
            cast(type[BaseModel], cls.bound_type)
        )  # This cast looks bad but is very benign because we're doing a packet lookup; if the class isn't of BaseModel type, then `None` must be returned anyway.

        if cls._packet_id is None:
            raise DeveloperException(
                f"`Layout` subclass (`{cls.__name__}`)'s generic type (`{cls.bound_type.__name__}`) is not a registered packet type. Ensure it inherits from `pydantic.BaseModel` and register the corresponding `Layout[...]` implementation with the `@register_layout(<packet_id>)` decorator."
            )

        cls._css_class = f"{cls._packet_id.lower().replace(' ', '-')}-layout"

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
        return cls

    return wrapper


def dispatch_layout(data: BaseModel) -> Layout:
    packet_id: PacketId = PacketAuthority.access_packet_id(data.__class__)
    layout_cls: type[Layout] = PacketAuthority.access_layout(packet_id)
    return layout_cls(data)
