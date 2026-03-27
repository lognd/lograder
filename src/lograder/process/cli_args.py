from types import EllipsisType
from typing import Any, Callable, Optional, Sequence, Iterable, TypedDict, TypeVar, cast

from pydantic import BaseModel, Field

from lograder.exception import DeveloperException
from lograder.common import Singleton

T = TypeVar("T")


class _PydanticCLIExtra(TypedDict):
    emit: Optional[Sequence[str]]
    emitter: Optional[Callable[[Any], Any]]

# noinspection PyPep8Naming
class CLI_ARG_MISSING(Singleton):
    ...

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

# noinspection PyPep8Naming
def CLIMultiOption(
        *,
        default: Iterable[T] | EllipsisType = ...,
        sequence_emit: Optional[Sequence[str | EllipsisType]] = (...,),
        sequence_emitter: Optional[Callable[[Iterable[T]], Sequence[str | EllipsisType]]] = None,
        token_emit: Optional[Sequence[str]] = ("{}",),
        token_emitter: Optional[Callable[[T], Sequence[str]]] = None,
        **field_kwargs: Any
) -> Any:
    if sequence_emit is None and sequence_emitter is None:
        raise DeveloperException(
            f"Keyword parameter `sequence_emit` and `sequence_emitter` cannot both be `None` in `CLIMultiOption`."
        )
    elif sequence_emit is not None and sequence_emitter is not None:
        raise DeveloperException(
            f"Keyword parameter `sequence_emit` ({sequence_emit}) and `sequence_emitter` ({sequence_emitter}) cannot both be specified in `CLIMultiOption`."
        )
    elif token_emit is None and token_emitter is None:
        raise DeveloperException(
            f"Keyword parameter `token_emit` and `token_emitter` cannot both be `None` in `CLIMultiOption`."
        )
    elif token_emit is not None and token_emitter is not None:
        raise DeveloperException(
            f"Keyword parameter `token_emit` ({token_emit}) and `token_emitter` ({token_emitter}) cannot both be specified in `CLIMultiOption`."
        )

    if sequence_emitter is None:
        sequence_emitter = lambda _: sequence_emit

    def emitter(input: Iterable[T]) -> Sequence[str]:
        base_sequence = sequence_emitter(input)
        new_sequence = []
        for token in base_sequence:
            if isinstance(token, EllipsisType):
                for item in input:
                    if token_emit is not None:
                        new_sequence.extend(t.format(item) for t in token_emit)
                        continue
                    new_sequence.extend(token_emitter(item))
            else:
                new_sequence.append(token)
        return new_sequence

    return CLIOption(
        default=default,
        emit=None,
        emitter=emitter,
        **field_kwargs
    )


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
