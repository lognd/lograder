from typing import Any, Optional, Type, TypeVar, Union, get_args, get_origin


def get_first_bound_type(typ: Type) -> Any:
    for base in getattr(typ, "__orig_bases__", ()):
        return get_args(base)[0]
    return None


def get_bound_types(cls: type, target_typ: type) -> Optional[tuple[Any, ...]]:
    return _get_bound_types_recursive(cls, target_typ, {})


def unwrap_union_types(typ: Type) -> set[Type]:
    origin = get_origin(typ)
    if origin is Union:
        return set(get_args(typ))
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
        return origin[new_args]
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
