from types import EllipsisType
from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    TypedDict,
    TypeVar,
    cast,
)

from pydantic import BaseModel, Field

from lograder.common import Singleton
from lograder.exception import DeveloperException

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class _PydanticCLIExtra(TypedDict):
    emit: Optional[Sequence[str]]
    emitter: Optional[Callable[[Any], Any]]


# noinspection PyPep8Naming
class CLI_ARG_MISSING(Singleton): ...


# noinspection PyPep8Naming
def CLIOption(
    *,
    default: T | EllipsisType = ...,
    emit: Optional[Sequence[str]] = ("{}",),
    emitter: Optional[Callable[[T], Sequence[str]]] = None,
    **field_kwargs: Any,
) -> Any:
    if emit is None and emitter is None:
        raise DeveloperException(
            "You must specify either an emit sequence or an emitter function when specifying a `CLIOption`."
        )

    _extra: Any = field_kwargs.pop("json_schema_extra", {})
    extra: dict = _extra if isinstance(_extra, dict) else {}
    extra["cli"] = _PydanticCLIExtra(emit=emit, emitter=emitter)
    return Field(default=default, json_schema_extra=extra, **field_kwargs)


def validate_single_specification(source: str, /, **kwargs: Any) -> None:
    if not kwargs:
        return

    specs: dict[str, Any] = {}
    for kw, arg in kwargs.items():
        if arg is not None:
            specs[kw] = arg

    if len(specs) == 1:
        return
    elif len(specs) == 0:
        raise DeveloperException(
            f"In `{source}`, parameters `{'`, `'.join(kwargs)}` cannot all be `None`."
        )

    raise DeveloperException(
        f"In `{source}`, only a single argument may be specified (not `None`) within the parameters of `{', '.join(f'`{k}` ({v} of type {v.__class__.__name__})' for k, v in kwargs.items())}`."
    )


# noinspection PyPep8Naming
def CLIMultiOption(
    *,
    default: Iterable[T] | EllipsisType = ...,
    sequence_emit: Optional[Sequence[str | EllipsisType]] = (...,),
    sequence_emitter: Optional[
        Callable[[Iterable[T]], Sequence[str | EllipsisType]]
    ] = None,
    token_emit: Optional[Sequence[str]] = ("{}",),
    token_emitter: Optional[Callable[[T], Sequence[str]]] = None,
    **field_kwargs: Any,
) -> Any:
    validate_single_specification(
        "CLIMultiOption", sequence_emit=sequence_emit, sequence_emitter=sequence_emitter
    )
    validate_single_specification(
        "CLIMultiOption", token_emit=token_emit, token_emitter=token_emitter
    )

    if sequence_emitter is None:
        assert sequence_emit is not None  # Must be true; we just validated.
        sequence_emitter = lambda _: sequence_emit
    assert (
        sequence_emitter is not None
    )  # Must be true; if it was originally None, then the branch above must have been taken.

    def emitter(input: Iterable[T]) -> Sequence[str]:
        base_sequence = sequence_emitter(input)
        new_sequence: list[str] = []
        for token in base_sequence:
            if isinstance(token, EllipsisType):
                for item in input:
                    if token_emit is not None:
                        new_sequence.extend(t.format(item) for t in token_emit)
                        continue
                    assert (
                        token_emitter is not None
                    )  # Must be true because we validate at the beginning of the surrounding function.
                    new_sequence.extend(token_emitter(item))
            else:
                new_sequence.append(token)
        return new_sequence

    return CLIOption(default=default, emit=None, emitter=emitter, **field_kwargs)


# noinspection PyPep8Naming
def CLIKVOption(
    *,
    default: Mapping[K, V] | EllipsisType = ...,
    sequence_emit: Optional[Sequence[str | EllipsisType]] = (...,),
    sequence_emitter: Optional[
        Callable[[Mapping[K, V]], Sequence[str | EllipsisType]]
    ] = None,
    token_emit: Optional[Sequence[str]] = ("{key}={value}",),
    token_emitter: Optional[Callable[[K, V], Sequence[str]]] = None,
    **field_kwargs: Any,
) -> Any:
    validate_single_specification(
        "CLIMultiOption", sequence_emit=sequence_emit, sequence_emitter=sequence_emitter
    )
    validate_single_specification(
        "CLIMultiOption", token_emit=token_emit, token_emitter=token_emitter
    )

    if sequence_emitter is None:
        assert sequence_emit is not None  # Must be true; we just validated.
        sequence_emitter = lambda _: sequence_emit
    assert (
        sequence_emitter is not None
    )  # Must be true; if it was originally None, then the branch above must have been taken.

    def emitter(input: Mapping[K, V]) -> Sequence[str]:
        base_sequence = sequence_emitter(input)
        new_sequence: list[str] = []
        for token in base_sequence:
            if isinstance(token, EllipsisType):
                for key, value in input.items():
                    if token_emit is not None:
                        new_sequence.extend(
                            t.format(k=key, v=value, key=key, value=value)
                            for t in token_emit
                        )
                        continue
                    assert (
                        token_emitter is not None
                    )  # Must be true because we validate at the beginning of the surrounding function.
                    new_sequence.extend(token_emitter(key, value))
            else:
                new_sequence.append(token)
        return new_sequence

    return CLIOption(default=default, emit=None, emitter=emitter, **field_kwargs)


# noinspection PyPep8Naming
def CLIPresenceFlag(
    emit: Sequence[str],
    *,
    default: T | EllipsisType = ...,
    present_when: bool = True,
    **field_kwargs: Any,
) -> Any:
    return CLIOption(
        default=default,
        emitter=lambda b: (
            emit if b and present_when or (not b and not present_when) else ()
        ),
        **field_kwargs,
    )


# noinspection PyPep8Naming
def CLIFlag(
    true: Sequence[str],
    false: Sequence[str],
    *,
    default: T | EllipsisType = ...,
    **field_kwargs: Any,
) -> Any:
    return CLIOption(
        default=default,
        emitter=lambda b: (
            () if b is not True and b is not False else true if b is True else false
        ),
        **field_kwargs,
    )


class CLIArgs(BaseModel):
    @classmethod
    def get_cli_schema(cls) -> dict[str, Callable[[Any], list[str]]]:
        schema = {}
        for name, field in cls.model_fields.items():
            if not hasattr(field, "json_schema_extra") or not isinstance(
                field.json_schema_extra, dict
            ):
                continue
            if "cli" in field.json_schema_extra:
                cli_data = cast(_PydanticCLIExtra, field.json_schema_extra["cli"])
                transformation: Callable[[Any], list[str]]
                if cli_data["emit"] is not None:

                    def transformation(v: Any) -> list[str]:
                        if v is CLI_ARG_MISSING():
                            return []
                        # noinspection PyUnnecessaryCast
                        return [
                            s.format(str(v)) for s in cast(list[str], cli_data["emit"])
                        ]

                elif cli_data["emitter"] is not None:
                    transformation = cli_data["emitter"]
                else:
                    raise DeveloperException(
                        f"This branch in `CLIArgs.get_cli_schema` should be unreachable, but just in case, the "
                        f"`CLIOption` or `CLIFlag` associated with field, `{name}`, did not specify an `emitter` nor"
                        f"an `emit` option."
                    )
                schema[name] = transformation
        return schema

    def emit(self) -> list[str]:
        cli_schema = self.get_cli_schema()
        arguments: list[str] = []
        for name, transformation in cli_schema.items():
            arguments.extend(transformation(getattr(self, name)))
        return arguments
