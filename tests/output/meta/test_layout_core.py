# type: ignore

from __future__ import annotations

import pytest
from pydantic import BaseModel

from lograder.exception import DeveloperException
from lograder.output.layout.layout import Layout, dispatch_layout, register_layout


class StreamPacket(BaseModel):
    name: str
    value: int


def test_layout_subclass_resolves_bound_type():
    class XLayout(Layout[StreamPacket]):
        @classmethod
        def to_ansi(cls, data: StreamPacket) -> str:
            return "ansi"

        @classmethod
        def to_simple(cls, data: StreamPacket) -> str:
            return "simple"

    assert XLayout.bound_type is StreamPacket


def test_register_layout_sets_css_class_and_registers():
    @register_layout("STREAM")
    class StreamLayout(Layout[StreamPacket]):
        @classmethod
        def to_ansi(cls, data: StreamPacket) -> str:
            return "ansi"

        @classmethod
        def to_simple(cls, data: StreamPacket) -> str:
            return "simple"

    assert StreamLayout._css_class == "stream-layout"


def test_layout_instance_stores_data():
    @register_layout("STREAM")
    class StreamLayout(Layout[StreamPacket]):
        @classmethod
        def to_ansi(cls, data: StreamPacket) -> str:
            return "ansi"

        @classmethod
        def to_simple(cls, data: StreamPacket) -> str:
            return "simple"

    data = StreamPacket(name="abc", value=5)
    layout = StreamLayout(data)
    assert layout.data == data


def test_layout_ansi_property_calls_to_ansi():
    @register_layout("STREAM")
    class StreamLayout(Layout[StreamPacket]):
        @classmethod
        def to_ansi(cls, data: StreamPacket) -> str:
            return f"A:{data.name}:{data.value}"

        @classmethod
        def to_simple(cls, data: StreamPacket) -> str:
            return "simple"

    layout = StreamLayout(StreamPacket(name="abc", value=5))
    assert layout.ansi == "A:abc:5"


def test_layout_simple_property_calls_to_simple():
    @register_layout("STREAM")
    class StreamLayout(Layout[StreamPacket]):
        @classmethod
        def to_ansi(cls, data: StreamPacket) -> str:
            return "ansi"

        @classmethod
        def to_simple(cls, data: StreamPacket) -> str:
            return f"S:{data.name}:{data.value}"

    layout = StreamLayout(StreamPacket(name="abc", value=5))
    assert layout.simple == "S:abc:5"


def test_layout_strip_ansi_removes_escape_codes():
    assert Layout.strip_ansi("a\x1b[31mred\x1b[0mb") == "aredb"


def test_layout_to_ascii_defaults_to_stripped_ansi():
    @register_layout("STREAM")
    class StreamLayout(Layout[StreamPacket]):
        @classmethod
        def to_ansi(cls, data: StreamPacket) -> str:
            return "\x1b[31mhello\x1b[0m"

        @classmethod
        def to_simple(cls, data: StreamPacket) -> str:
            return "simple"

    assert StreamLayout.to_ascii(StreamPacket(name="x", value=1)) == "hello"


def test_layout_ascii_property_uses_to_ascii():
    @register_layout("STREAM")
    class StreamLayout(Layout[StreamPacket]):
        @classmethod
        def to_ansi(cls, data: StreamPacket) -> str:
            return "\x1b[32mabc\x1b[0m"

        @classmethod
        def to_simple(cls, data: StreamPacket) -> str:
            return "simple"

    layout = StreamLayout(StreamPacket(name="x", value=1))
    assert layout.ascii == "abc"


def test_layout_to_html_wraps_converted_ansi(monkeypatch):
    @register_layout("STREAM")
    class StreamLayout(Layout[StreamPacket]):
        @classmethod
        def to_ansi(cls, data: StreamPacket) -> str:
            return "\x1b[31mhello\x1b[0m"

        @classmethod
        def to_simple(cls, data: StreamPacket) -> str:
            return "simple"

    from lograder.output.layout import layout as layout_mod

    monkeypatch.setattr(
        layout_mod._ANSI2HTML,
        "convert",
        lambda text, full=False: f"<span>{text}</span>",
    )

    html = StreamLayout.to_html(StreamPacket(name="x", value=1))
    assert html == (
        '<pre class="stream-layout layout-all"><span>\x1b[31mhello\x1b[0m</span></pre>'
    )


def test_layout_html_property_uses_to_html(monkeypatch):
    @register_layout("STREAM")
    class StreamLayout(Layout[StreamPacket]):
        @classmethod
        def to_ansi(cls, data: StreamPacket) -> str:
            return "hello"

        @classmethod
        def to_simple(cls, data: StreamPacket) -> str:
            return "simple"

    from lograder.output.layout import layout as layout_mod

    monkeypatch.setattr(
        layout_mod._ANSI2HTML,
        "convert",
        lambda text, full=False: "<i>hello</i>",
    )

    layout = StreamLayout(StreamPacket(name="x", value=1))
    assert layout.html == '<pre class="stream-layout layout-all"><i>hello</i></pre>'


def test_layout_to_html_rejects_missing_bound_type():
    class FakeLayout(Layout):
        @classmethod
        def to_ansi(cls, data):
            return "ansi"

        @classmethod
        def to_simple(cls, data):
            return "simple"

    FakeLayout.bound_type = None

    with pytest.raises(DeveloperException, match="must specify generic type"):
        FakeLayout.to_html(StreamPacket(name="x", value=1))


def test_register_layout_rejects_layout_without_generic_type():
    class UngenericLayout(Layout):
        @classmethod
        def to_ansi(cls, data):
            return "ansi"

        @classmethod
        def to_simple(cls, data):
            return "simple"

    UngenericLayout.bound_type = None

    with pytest.raises(DeveloperException, match="must specify generic type"):
        register_layout("STREAM")(UngenericLayout)


def test_dispatch_layout_returns_registered_layout_instance():
    @register_layout("STREAM")
    class StreamLayout(Layout[StreamPacket]):
        @classmethod
        def to_ansi(cls, data: StreamPacket) -> str:
            return "ansi"

        @classmethod
        def to_simple(cls, data: StreamPacket) -> str:
            return "simple"

    data = StreamPacket(name="abc", value=10)
    layout = dispatch_layout(data)

    assert isinstance(layout, StreamLayout)
    assert layout.data == data


def test_dispatch_layout_raises_when_packet_type_has_no_registered_id():
    data = StreamPacket(name="abc", value=10)

    with pytest.raises(DeveloperException, match="missing a `PacketId`"):
        dispatch_layout(data)
