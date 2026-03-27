from lograder.common.empty import Empty, Unreachable
from lograder.common.generic_utils import (
    get_args,
    get_bound_types,
    get_first_bound_type,
    get_origin,
    unwrap_union_types,
    write_generic_type,
)
from lograder.common.result import Err, Ok, Result

__all__ = [
    "Result",
    "Empty",
    "Unreachable",
    "Ok",
    "Err",
    "get_first_bound_type",
    "get_bound_types",
    "unwrap_union_types",
    "get_origin",
    "get_args",
    "write_generic_type",
]
