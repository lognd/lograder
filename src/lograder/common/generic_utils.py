from types import UnionType
from typing import (
    Any,
    Optional,
    TypeVar,
    Union,
    cast,
)
from typing import get_args as typing_get_args
from typing import get_origin as typing_get_origin

RUNTIME_ORIGIN_ATTR = "__runtime_origin__"
RUNTIME_ARGS_ATTR = "__runtime_args__"


def get_origin(tp: type) -> Optional[type]:
    if hasattr(tp, RUNTIME_ORIGIN_ATTR):
        return cast(type, getattr(tp, RUNTIME_ORIGIN_ATTR))
    return typing_get_origin(tp)


def get_args(tp: type) -> tuple[Any, ...]:
    if hasattr(tp, RUNTIME_ARGS_ATTR):
        args = getattr(tp, RUNTIME_ARGS_ATTR)
        if args is None:
            return ()
        return tuple(args)
    return typing_get_args(tp)


def set_typeinfo(
    tp: type,
    *,
    origin: type | None,
    args: tuple[Any, ...] | list[Any] | None,
) -> type:
    setattr(tp, RUNTIME_ORIGIN_ATTR, origin)
    setattr(tp, RUNTIME_ARGS_ATTR, tuple(args) if args is not None else ())
    return tp


def write_generic_type(
    *,
    cls: type,
    generic_type: type,
    args: tuple[Any, ...] | list[Any] | None,
) -> type:
    orig_bases = list(getattr(cls, "__orig_bases__", ()))
    try:
        index, _ = next(
            (i, item)
            for i, item in enumerate(orig_bases)
            if get_origin(item) is generic_type
        )
    except StopIteration:
        index = -1

    generic_type = set_typeinfo(generic_type, origin=generic_type, args=args)
    if index != -1:
        orig_bases.pop(index)
        orig_bases.insert(index, generic_type)
    else:
        orig_bases.append(generic_type)

    setattr(cls, "__orig_bases__", tuple(orig_bases))
    return cls


def get_first_bound_type(typ: type) -> Any:
    for base in getattr(typ, "__orig_bases__", ()):
        origin = get_origin(base)
        args = get_args(base)
        if origin is not None and args:
            return args[0]
    return None


def get_bound_types(cls: type, target_typ: type) -> Optional[tuple[Any, ...]]:
    return _get_bound_types_recursive(cls, target_typ, {})


def unwrap_union_types(typ: Any) -> set[Any]:
    origin = get_origin(typ)

    if origin in (Union, UnionType):
        out: set[Any] = set()
        for arg in get_args(typ):
            out.update(unwrap_union_types(arg))
        return out

    return {typ}


def _substitute_typevars(tp: Any, mapping: dict[TypeVar, Any]) -> Any:
    if isinstance(tp, TypeVar):
        return mapping.get(tp, tp)

    origin = get_origin(tp)
    if origin is None:
        return mapping.get(tp, tp)

    args = get_args(tp)
    if not args:
        return tp

    new_args = tuple(_substitute_typevars(arg, mapping) for arg in args)

    try:
        return origin[new_args]  # type: ignore[index]
    except Exception:
        return tp


def _get_bound_types_recursive(
    cls: type,
    target_typ: type,
    mapping: dict[TypeVar, Any],
) -> Optional[tuple[Any, ...]]:
    for base in getattr(cls, "__orig_bases__", ()):
        origin = get_origin(base)
        if origin is None:
            continue

        raw_args = get_args(base)
        args = tuple(_substitute_typevars(arg, mapping) for arg in raw_args)

        if origin is target_typ:
            return args

        if isinstance(origin, type) and issubclass(origin, target_typ):
            params = getattr(origin, "__parameters__", ())
            next_mapping = dict(mapping)
            next_mapping.update(zip(params, args))

            found = _get_bound_types_recursive(origin, target_typ, next_mapping)
            if found is not None:
                return found

    return None
