from __future__ import annotations

from abc import ABCMeta
from typing import Any, MutableMapping, cast, no_type_check

from pydantic import BaseModel

from lograder.common import write_generic_type
from lograder.output.layout.layout import Layout, LayoutLike, register_layout


# noinspection PyPep8Naming
class _UNREACHABLE_DUMMY_MODEL(BaseModel): ...


@no_type_check
def make_dynamic_layout(
    *,
    layout_id: str,
    layout_type: type[BaseModel],
    layout_cls_name: str,
    layout_like: LayoutLike,
) -> type[Layout]:
    class NewLayoutMeta(ABCMeta):
        @classmethod
        def __prepare__(
            mcs, name: str, bases: tuple[type, ...], /, **kwds: Any
        ) -> MutableMapping[str, object]:
            return {"__meta_bound_type__": layout_type}

    class NewLayout(Layout[_UNREACHABLE_DUMMY_MODEL], metaclass=NewLayoutMeta):
        to_ansi = layout_like.to_ansi
        to_simple = layout_like.to_simple
        if layout_like.to_ascii is not None:
            to_ascii = layout_like.to_ascii
        if layout_like.to_html is not None:
            to_html = layout_like.to_html

    NewLayout.__name__ = layout_cls_name
    NewLayout.__qualname__ = layout_cls_name
    NewLayout = write_generic_type(  # type: ignore[misc]
        cls=NewLayout, generic_type=Layout, args=(layout_type,)
    )
    # noinspection PyUnnecessaryCast
    NewLayout = cast(  # type: ignore[misc]
        type[Layout], register_layout(layout_id)(cast(type[Layout], NewLayout))
    )

    return NewLayout
