from __future__ import annotations

from typing import TYPE_CHECKING, Callable, NewType, Optional, Type, TypedDict

from pydantic import BaseModel

from ..exception import DeveloperException

if TYPE_CHECKING:
    from .layout import Layout

PacketId = NewType("PacketId", str)


class Packet(TypedDict):
    header: str
    payload: dict


def get_packet_id(packet: Packet) -> PacketId:
    return PacketId(packet.get("header", "unknown"))


class PacketAuthority:
    _f_lookup: dict[Type[BaseModel], PacketId] = {}
    _r_lookup: dict[PacketId, Type[BaseModel]] = {}
    _l_lookup: dict[PacketId, Type[Layout]] = {}

    @classmethod
    def register(cls, packet_id: PacketId, packet_layout: Type[Layout]) -> None:
        cls._l_lookup[packet_id] = packet_layout
        packet_cls = packet_layout.bound_type
        if packet_cls is None:
            packet_layout_name = packet_layout.__name__
            if packet_layout_name == "Layout":
                raise DeveloperException(
                    "`PacketAuthority` must only register `Layout` subclasses (not `Layout` generic class itself)."
                )
            raise DeveloperException(
                f"`Layout` subclass (`{packet_layout_name}`) must specify generic type, i.e. `Layout[Stream]` rather that merely `Layout`."
            )
        cls._f_lookup[packet_cls] = packet_id
        cls._r_lookup[packet_id] = packet_cls

    @classmethod
    def get_class(cls, packet_id: PacketId) -> Optional[Type[BaseModel]]:
        return cls._r_lookup.get(packet_id)

    @classmethod
    def access_class(cls, packet_id: PacketId) -> Type[BaseModel]:
        data_type = cls.get_class(packet_id)
        if data_type is None:
            raise DeveloperException(
                f"A logging packet identifier (`{packet_id}`) was found missing a registered `pydantic.BaseModel`, set with `@register_layout(<packet_id>)` decorator used on a class implementing the `Layout[<packet-type>]` generic."
            )
        return data_type

    @classmethod
    def get_packet_id(cls, packet_cls: Type[BaseModel]) -> Optional[PacketId]:
        return cls._f_lookup.get(packet_cls)

    @classmethod
    def access_packet_id(cls, packet_cls: Type[BaseModel]) -> PacketId:
        packet_id = cls.get_packet_id(packet_cls)
        if packet_id is None:
            raise DeveloperException(
                f"A logging packet type (`{packet_cls.__class__.__name__}`) was found missing a `PacketId`, set with `@register_layout(<packet_id>)` decorator used on a class implementing the `Layout[{packet_cls.__class__.__name__}]` generic."
            )
        return packet_id

    @classmethod
    def get_layout(cls, packet_id: PacketId) -> Optional[Type[Layout]]:
        return cls._l_lookup.get(packet_id)

    @classmethod
    def access_layout(cls, packet_id: PacketId) -> Type[Layout]:
        layout_cls = cls.get_layout(packet_id)
        if layout_cls is None:
            raise DeveloperException(
                f"A logging packet identifier (`{packet_id}`) was found missing a registered `Layout`, set with `@register_layout(<packet_id>)` decorator used on a class implementing the `Layout[<pydantic.BaseModel>]` generic."
            )
        return layout_cls


def wrap_packet(obj: BaseModel) -> Packet:
    packet_id = PacketAuthority.access_packet_id(obj.__class__)
    return {"header": str(packet_id), "payload": obj.model_dump()}


def unwrap_packet(packet: Packet) -> BaseModel:
    packet_id = get_packet_id(packet)
    cls = PacketAuthority.access_class(packet_id)
    return cls.model_validate(packet["payload"])
