from typing import Any, Optional, Type, Union, get_args, get_origin


def get_first_bound_type(typ: Type) -> Any:
    for base in getattr(typ, "__orig_bases__", ()):
        return get_args(base)[0]
    return None


def get_bound_types(cls: type, target_typ: Type) -> Optional[tuple[Any, ...]]:
    for base in getattr(cls, "__orig_bases__", ()):
        if get_origin(base) is not target_typ:
            continue
        args = get_args(base)
        return tuple(args)
    return None


def unwrap_union_types(typ: Type) -> set[Type]:
    origin = get_origin(typ)
    if origin is Union:
        return set(get_args(typ))
    return {typ}
