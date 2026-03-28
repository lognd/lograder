# type: ignore

from __future__ import annotations

import logging

import pytest
from pydantic import BaseModel

from lograder.exception import DeveloperException
from lograder.output.formatters import PacketFormatter
from lograder.output.layout.layout import Layout, register_layout
from lograder.output.logger import LograderLogger
from lograder.output.packets import wrap_packet


class FmtPacket(BaseModel):
    name: str


@register_layout("FMT")
class FmtLayout(Layout[FmtPacket]):
    @classmethod
    def to_ansi(cls, data: FmtPacket) -> str:
        return "ANSI!"

    @classmethod
    def to_simple(cls, data: FmtPacket) -> str:
        return "SIMPLE!"


def make_record(*, msg: str = "hello", level: int = logging.INFO) -> logging.LogRecord:
    return logging.LogRecord(
        name="test",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )


def test_packet_formatter_falls_back_without_packet():
    formatter = PacketFormatter(mode="simple")
    record = make_record(msg="plain message", level=logging.WARNING)

    assert formatter.format(record) == "WARNING: plain message"


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("simple", "SIMPLE!"),
        ("ansi", "ANSI!"),
        ("ascii", "ANSI!"),
    ],
)
def test_packet_formatter_formats_packet_modes(mode, expected):
    formatter = PacketFormatter(mode=mode)
    record = make_record(msg="ignored")
    packet = wrap_packet(FmtPacket(name="abc"))
    setattr(record, LograderLogger.PACKET_ATTR, packet)

    assert formatter.format(record) == expected


def test_packet_formatter_html_mode(monkeypatch):
    formatter = PacketFormatter(mode="html")
    record = make_record(msg="ignored")
    packet = wrap_packet(FmtPacket(name="abc"))
    setattr(record, LograderLogger.PACKET_ATTR, packet)

    from lograder.output.layout import layout as layout_mod

    monkeypatch.setattr(
        layout_mod._ANSI2HTML,
        "convert",
        lambda text, full=False: "<b>ANSI!</b>",
    )

    assert (
        formatter.format(record)
        == '<pre class="fmt-layout layout-all"><b>ANSI!</b></pre>'
    )


def test_packet_formatter_rejects_none_output(monkeypatch):
    formatter = PacketFormatter(mode="simple")
    record = make_record()

    class DummyLayout:
        simple = None

    monkeypatch.setattr(
        "lograder.output.formatters.unwrap_packet", lambda packet: object()
    )
    monkeypatch.setattr(
        "lograder.output.formatters.dispatch_layout", lambda data: DummyLayout()
    )

    setattr(record, LograderLogger.PACKET_ATTR, {"header": "X", "payload": {}})

    with pytest.raises(DeveloperException, match="does not support an output of type"):
        formatter.format(record)


def test_packet_formatter_rejects_non_string_output(monkeypatch):
    formatter = PacketFormatter(mode="simple")
    record = make_record()

    class DummyLayout:
        simple = 123

    monkeypatch.setattr(
        "lograder.output.formatters.unwrap_packet", lambda packet: object()
    )
    monkeypatch.setattr(
        "lograder.output.formatters.dispatch_layout", lambda data: DummyLayout()
    )

    setattr(record, LograderLogger.PACKET_ATTR, {"header": "X", "payload": {}})

    with pytest.raises(
        DeveloperException,
        match="is malformed; output type of `simple` property is not a `str`",
    ):
        formatter.format(record)
