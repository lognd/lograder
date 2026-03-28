# type: ignore

from __future__ import annotations

from pydantic import BaseModel

from lograder.output.layout.dynamic import make_dynamic_layout
from lograder.output.layout.layout import LayoutLike, dispatch_layout


class DynamicPacket(BaseModel):
    label: str
    score: int


def test_make_dynamic_layout_creates_registered_layout():
    layout_like = LayoutLike(
        to_ansi=lambda cls, data: f"\x1b[31m{data.label}:{data.score}\x1b[0m",
        to_simple=lambda cls, data: f"{data.label}:{data.score}",
    )

    layout_cls = make_dynamic_layout(
        layout_id="DYN",
        layout_type=DynamicPacket,
        layout_cls_name="DynamicPacketLayout",
        layout_like=layout_like,
    )

    assert layout_cls.__name__ == "DynamicPacketLayout"
    assert layout_cls.__qualname__ == "DynamicPacketLayout"
    assert layout_cls.bound_type is DynamicPacket
    assert layout_cls._css_class == "dyn-layout"


def test_make_dynamic_layout_default_ascii_comes_from_base():
    layout_like = LayoutLike(
        to_ansi=lambda cls, data: "\x1b[32mHELLO\x1b[0m",
        to_simple=lambda cls, data: "simple",
    )

    layout_cls = make_dynamic_layout(
        layout_id="DYN",
        layout_type=DynamicPacket,
        layout_cls_name="DynamicPacketLayout",
        layout_like=layout_like,
    )

    layout = layout_cls(DynamicPacket(label="a", score=1))
    assert layout.ascii == "HELLO"


def test_make_dynamic_layout_uses_custom_ascii_when_provided():
    layout_like = LayoutLike(
        to_ansi=lambda cls, data: "\x1b[32mHELLO\x1b[0m",
        to_simple=lambda cls, data: "simple",
        to_ascii=lambda cls, data: "CUSTOM_ASCII",
    )

    layout_cls = make_dynamic_layout(
        layout_id="DYN",
        layout_type=DynamicPacket,
        layout_cls_name="DynamicPacketLayout",
        layout_like=layout_like,
    )

    layout = layout_cls(DynamicPacket(label="a", score=1))
    assert layout.ascii == "CUSTOM_ASCII"


def test_make_dynamic_layout_uses_custom_html_when_provided():
    layout_like = LayoutLike(
        to_ansi=lambda cls, data: "ansi",
        to_simple=lambda cls, data: "simple",
        to_html=lambda cls, data: "<div>custom html</div>",
    )

    layout_cls = make_dynamic_layout(
        layout_id="DYN",
        layout_type=DynamicPacket,
        layout_cls_name="DynamicPacketLayout",
        layout_like=layout_like,
    )

    layout = layout_cls(DynamicPacket(label="a", score=1))
    assert layout.html == "<div>custom html</div>"


def test_make_dynamic_layout_dispatch_integration():
    layout_like = LayoutLike(
        to_ansi=lambda cls, data: "ansi",
        to_simple=lambda cls, data: f"{data.label}:{data.score}",
    )

    layout_cls = make_dynamic_layout(
        layout_id="DYN",
        layout_type=DynamicPacket,
        layout_cls_name="DynamicPacketLayout",
        layout_like=layout_like,
    )

    obj = DynamicPacket(label="alice", score=4)
    layout = dispatch_layout(obj)

    assert isinstance(layout, layout_cls)
    assert layout.simple == "alice:4"
