from types import EllipsisType
from typing import (
    Any,
    Callable,
    Iterable,
    Literal,
    Mapping,
    Optional,
    Sequence,
    TypedDict,
    TypeVar,
    cast,
)

from pydantic import BaseModel, ConfigDict, Field

from lograder.common import Singleton
from lograder.exception import DeveloperException

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


# noinspection PyPep8Naming
class CLI_ARG_MISSING(Singleton): ...


# noinspection PyPep8Naming
class POSITION_AGNOSTIC(Singleton): ...


ArgumentPosition = int | POSITION_AGNOSTIC


class _PydanticCLIExtra(TypedDict):
    emit: Optional[Sequence[str]]
    emitter: Optional[Callable[[Any], Any]]
    position: ArgumentPosition


CLITransformation = Callable[[Any], list[str]]
CLISchema = dict[str, tuple[ArgumentPosition, CLITransformation]]


def _is_position_agnostic(position: ArgumentPosition) -> bool:
    return isinstance(position, POSITION_AGNOSTIC)


def _validate_declared_positions(cls_name: str, schema: CLISchema) -> None:
    """
    Checks what can be known at class-definition time.

    We can reject:
    - duplicate declared explicit positions
    - positions that are impossible even in the best case
      (e.g. position=10 when the class only has 4 CLI fields total)
    """
    num_declared_fields = len(schema)
    seen: dict[int, str] = {}

    for field_name, (position, _) in schema.items():
        if _is_position_agnostic(position):
            continue

        assert isinstance(position, int)

        if position in seen:
            other = seen[position]
            raise DeveloperException(
                f"In `{cls_name}`, fields `{other}` and `{field_name}` both declare CLI position "
                f"`{position}`. Two CLI fields cannot declare the same explicit position."
            )
        seen[position] = field_name

        # Impossible positive index even if every CLI field emits.
        if position >= 0 and position >= num_declared_fields:
            raise DeveloperException(
                f"In `{cls_name}`, field `{field_name}` declares CLI position `{position}`, but the class only has "
                f"{num_declared_fields} CLI field(s). That position can never exist."
            )

        # Impossible negative index even if every CLI field emits.
        if position < 0 and (-position) > num_declared_fields:
            raise DeveloperException(
                f"In `{cls_name}`, field `{field_name}` declares CLI position `{position}`, but the class only has "
                f"{num_declared_fields} CLI field(s). That position can never exist."
            )


def _order_emitted_arguments(
    cls_name: str,
    emitted: list[tuple[str, ArgumentPosition, list[str]]],
) -> list[str]:
    """
    `emitted` is a list of:
        (field_name, declared_position, emitted_tokens)

    Positioning is by emitted field-block, not by individual token.
    """
    if not emitted:
        return []

    num_blocks = len(emitted)
    resolved_positions: dict[int, tuple[str, list[str]]] = {}
    agnostic_blocks: list[tuple[str, list[str]]] = []

    for field_name, position, tokens in emitted:
        if _is_position_agnostic(position):
            agnostic_blocks.append((field_name, tokens))
            continue

        assert isinstance(position, int)

        resolved = position if position >= 0 else (num_blocks + position)

        if resolved < 0 or resolved >= num_blocks:
            raise DeveloperException(
                f"In `{cls_name}`, field `{field_name}` resolved to CLI position `{resolved}` from declared "
                f"position `{position}`, but this instance only emitted {num_blocks} argument block(s)."
            )

        if resolved in resolved_positions:
            other_name, _ = resolved_positions[resolved]
            raise DeveloperException(
                f"In `{cls_name}`, emitted fields `{other_name}` and `{field_name}` both resolved to CLI position "
                f"`{resolved}` for this instance. This usually happens when a positive and negative position overlap "
                f"(for example `0` and `-2` with only two emitted fields)."
            )

        resolved_positions[resolved] = (field_name, tokens)

    ordered_blocks: list[Optional[list[str]]] = [None] * num_blocks

    for index, (_, tokens) in resolved_positions.items():
        ordered_blocks[index] = tokens

    agnostic_index = 0
    for i in range(num_blocks):
        if ordered_blocks[i] is None:
            if agnostic_index >= len(agnostic_blocks):
                raise DeveloperException(
                    f"Internal error while ordering CLI arguments for `{cls_name}`: not enough agnostic blocks."
                )
            ordered_blocks[i] = agnostic_blocks[agnostic_index][1]
            agnostic_index += 1

    if agnostic_index != len(agnostic_blocks):
        raise DeveloperException(
            f"Internal error while ordering CLI arguments for `{cls_name}`: too many agnostic blocks remained."
        )

    arguments: list[str] = []
    for block in ordered_blocks:
        assert block is not None
        arguments.extend(block)

    return arguments


# noinspection PyPep8Naming
def CLIOption(
    *,
    default: T | EllipsisType = ...,
    emit: Optional[Sequence[str]] = ("{}",),
    emitter: Optional[Callable[[T], Sequence[str]]] = None,
    position: ArgumentPosition = POSITION_AGNOSTIC(),
    **field_kwargs: Any,
) -> Any:
    if emit is None and emitter is None:
        raise DeveloperException(
            "You must specify either an emit sequence or an emitter function when specifying a `CLIOption`."
        )

    _extra: Any = field_kwargs.pop("json_schema_extra", {})
    extra: dict = _extra if isinstance(_extra, dict) else {}
    extra["cli"] = _PydanticCLIExtra(emit=emit, emitter=emitter, position=position)
    return Field(default=default, json_schema_extra=extra, **field_kwargs)


def validate_single_specification(source: str, /, **kwargs: Any) -> None:
    if not kwargs:
        return

    specs: dict[str, Any] = {}
    for kw, arg in kwargs.items():
        if arg is not None:
            specs[kw] = arg

    if len(specs) == 0:
        raise DeveloperException(
            f"In `{source}`, parameters `{'`, `'.join(kwargs)}` cannot all be `None`."
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
    position: ArgumentPosition = POSITION_AGNOSTIC(),
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

    return CLIOption(
        default=default, emit=None, emitter=emitter, position=position, **field_kwargs
    )


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
    position: ArgumentPosition = POSITION_AGNOSTIC(),
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

    return CLIOption(
        default=default, emit=None, emitter=emitter, position=position, **field_kwargs
    )


# noinspection PyPep8Naming
def CLIPresenceFlag(
    emit: Sequence[str],
    *,
    default: T | EllipsisType = ...,
    present_when: bool = True,
    position: ArgumentPosition = POSITION_AGNOSTIC(),
    **field_kwargs: Any,
) -> Any:
    return CLIOption(
        default=default,
        emitter=lambda b: (
            emit if b and present_when or (not b and not present_when) else ()
        ),
        position=position,
        **field_kwargs,
    )


# noinspection PyPep8Naming
def CLIFlag(
    true: Sequence[str],
    false: Sequence[str],
    *,
    default: T | EllipsisType = ...,
    position: ArgumentPosition = POSITION_AGNOSTIC(),
    **field_kwargs: Any,
) -> Any:
    return CLIOption(
        default=default,
        emitter=lambda b: (
            () if b is not True and b is not False else true if b is True else false
        ),
        position=position,
        **field_kwargs,
    )


class CLIArgs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        cls.get_cli_schema()  # forces definition-time validation

    @classmethod
    def get_cli_schema(cls) -> CLISchema:
        schema: CLISchema = {}
        for name, field in cls.model_fields.items():
            if not hasattr(field, "json_schema_extra") or not isinstance(
                field.json_schema_extra, dict
            ):
                continue
            if "cli" in field.json_schema_extra:
                cli_data = cast(_PydanticCLIExtra, field.json_schema_extra["cli"])
                transformation: Callable[[Any], list[str]]
                if cli_data["emitter"] is None:
                    emit = cli_data["emit"]
                    # Must be true because `CLIOption` requires either `emitter` or `emit` to exist.
                    assert emit is not None

                    # noinspection PyUnnecessaryCast
                    def transformation(
                        v: Any,
                        emit: Sequence[str] = cast(Sequence[str], cli_data["emit"]),
                    ) -> list[str]:
                        if v is CLI_ARG_MISSING():
                            return []
                        # noinspection PyUnnecessaryCast
                        return [s.format(str(v)) for s in cast(list[str], emit)]

                elif cli_data["emitter"] is not None:
                    transformation = cli_data["emitter"]
                else:
                    raise DeveloperException(
                        f"This branch in `CLIArgs.get_cli_schema` should be unreachable, but just in case, the "
                        f"`CLIOption` or `CLIFlag` associated with field, `{name}`, did not specify an `emitter` nor"
                        f"an `emit` option."
                    )
                schema[name] = (cli_data["position"], transformation)

        _validate_declared_positions(cls.__name__, schema)
        return schema

    def emit(self) -> list[str]:
        cli_schema = self.get_cli_schema()
        emitted: list[tuple[str, ArgumentPosition, list[str]]] = []

        for name, (position, transformation) in cli_schema.items():
            new_args = transformation(getattr(self, name))

            if isinstance(new_args, str):
                raise DeveloperException(
                    f"The output of field `{name}` for `{self.__class__.__name__}` was found to be a `str`. This is almost certainly not what you meant. "
                    f"Please wrap your string in `Sequence` (like a `list` or `tuple`) because the bad default behavior would be treating each character like "
                    f"it is a separate token."
                )
            if "" in new_args:
                raise DeveloperException(
                    f"The output of field `{name}` for `{self.__class__.__name__}` had an empty string token inside. This is almost certainly not what you meant. "
                    f"Please ensure that you cannot output an empty string token. (For instance, output `[]` rather than `['']`."
                )

            if not new_args:
                continue

            emitted.append((name, position, list(new_args)))

        return _order_emitted_arguments(self.__class__.__name__, emitted)
