# mypy: ignore-errors
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


# ---------------------------------------------------------------------------
# Auto-registration via lograder.output.layout import
# ---------------------------------------------------------------------------


def test_uncaught_exception_layout_registered_by_init_import():
    # Regression: UncaughtException had no bottom-import in local_directory.py,
    # so pipelines that failed at LocalDirectory raised a confusing
    # "ModelMetaclass missing PacketId" error instead of showing the real cause.
    from lograder.exception import UncaughtException
    from lograder.output.packets import PacketAuthority

    assert PacketAuthority.get_packet_id(UncaughtException) is not None


def test_output_compare_layouts_registered_by_init_import():
    from lograder.output.packets import PacketAuthority
    from lograder.pipeline.test.output_compare import (
        OutputCompareError,
        OutputCompareFailure,
        OutputCompareSuccess,
    )

    for cls in (OutputCompareSuccess, OutputCompareFailure, OutputCompareError):
        assert PacketAuthority.get_packet_id(cls) is not None, (
            f"{cls.__name__} layout not registered after importing lograder.output.layout"
        )


def test_all_builtin_layouts_registered_by_init_import():
    # Importing from lograder.output.layout should register every built-in packet
    # type so pipeline authors never need manual layout imports in their pipelines.
    from lograder.output.packets import PacketAuthority
    from lograder.pipeline.build.bash_script import (
        BashScriptBuildError,
        BashScriptBuildOutput,
    )
    from lograder.pipeline.build.build import BuildOutput
    from lograder.pipeline.mixin.mixin import MixinData
    from lograder.pipeline.test.catch2 import Catch2Error, Catch2Failure, Catch2Success

    for cls in (
        BuildOutput,
        BashScriptBuildOutput,
        BashScriptBuildError,
        MixinData,
        Catch2Success,
        Catch2Failure,
        Catch2Error,
    ):
        assert PacketAuthority.get_packet_id(cls) is not None, (
            f"{cls.__name__} layout not registered after importing lograder.output.layout"
        )
