# type: ignore

from __future__ import annotations

import pytest
from pydantic import BaseModel

from lograder.exception import DeveloperException
from lograder.output.layout import Layout
from lograder.output.packets import (
    PacketAuthority,
    PacketId,
    get_packet_id,
    unwrap_packet,
    wrap_packet,
)


class PacketModel(BaseModel):
    x: int
    y: str


class PacketModel2(BaseModel):
    z: float


def test_get_packet_id_returns_header():
    packet = {"header": "ABC", "payload": {}}
    assert get_packet_id(packet) == PacketId("ABC")


def test_get_packet_id_defaults_to_unknown():
    packet = {"payload": {}}
    assert get_packet_id(packet) == PacketId("unknown")


def test_packet_authority_register_populates_all_lookups():
    class DummyLayout:
        __name__ = "DummyLayout"
        bound_type = PacketModel

    PacketAuthority.register(PacketId("PACKET"), DummyLayout)  # type: ignore[arg-type]

    assert PacketAuthority._l_lookup[PacketId("PACKET")] is DummyLayout
    assert PacketAuthority._f_lookup[PacketModel] == PacketId("PACKET")
    assert PacketAuthority._r_lookup[PacketId("PACKET")] is PacketModel


def test_packet_authority_register_rejects_layout_base_with_missing_bound_type():
    with pytest.raises(
        DeveloperException,
        match="must only register `Layout` subclasses",
    ):
        PacketAuthority.register(PacketId("P"), Layout)  # type: ignore[arg-type]


def test_packet_authority_register_rejects_unbound_layout_subclass():
    class DummyLayout:
        __name__ = "SomeLayout"
        bound_type = None

    with pytest.raises(DeveloperException, match="must specify generic type"):
        PacketAuthority.register(PacketId("P"), DummyLayout)  # type: ignore[arg-type]


def test_get_class_returns_none_when_missing():
    assert PacketAuthority.get_class(PacketId("MISSING")) is None


def test_access_class_raises_when_missing():
    with pytest.raises(
        DeveloperException, match="missing a registered `pydantic.BaseModel`"
    ):
        PacketAuthority.access_class(PacketId("MISSING"))


def test_get_packet_id_returns_none_when_missing():
    assert PacketAuthority.get_packet_id(PacketModel) is None


def test_access_packet_id_raises_when_missing():
    with pytest.raises(DeveloperException, match="missing a `PacketId`"):
        PacketAuthority.access_packet_id(PacketModel)


def test_get_layout_returns_none_when_missing():
    assert PacketAuthority.get_layout(PacketId("MISSING")) is None


def test_access_layout_raises_when_missing():
    with pytest.raises(DeveloperException, match="missing a registered `Layout`"):
        PacketAuthority.access_layout(PacketId("MISSING"))


def test_wrap_packet_round_trip():
    class DummyLayout:
        __name__ = "DummyLayout"
        bound_type = PacketModel

    PacketAuthority.register(PacketId("PACKET"), DummyLayout)  # type: ignore[arg-type]

    obj = PacketModel(x=1, y="two")
    packet = wrap_packet(obj)

    assert packet == {
        "header": "PACKET",
        "payload": {"x": 1, "y": "two"},
    }

    restored = unwrap_packet(packet)
    assert isinstance(restored, PacketModel)
    assert restored == obj


def test_wrap_packet_raises_when_packet_id_missing():
    with pytest.raises(DeveloperException, match="missing a `PacketId`"):
        wrap_packet(PacketModel(x=1, y="two"))


def test_unwrap_packet_raises_when_header_unknown():
    with pytest.raises(
        DeveloperException, match="missing a registered `pydantic.BaseModel`"
    ):
        unwrap_packet({"header": "UNKNOWN", "payload": {"x": 1, "y": "two"}})


def test_unwrap_packet_validates_payload_through_model():
    class DummyLayout:
        __name__ = "DummyLayout"
        bound_type = PacketModel2

    PacketAuthority.register(PacketId("P2"), DummyLayout)  # type: ignore[arg-type]

    result = unwrap_packet({"header": "P2", "payload": {"z": "1.5"}})
    assert isinstance(result, PacketModel2)
    assert result.z == 1.5
