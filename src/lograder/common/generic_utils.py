from typing import Type, Any, get_args

def get_bound_type(cls: Type) -> Any:
    for base in getattr(cls, "__orig_bases__", ()):
        return get_args(base)[0]
    return None