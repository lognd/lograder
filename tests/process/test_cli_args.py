# type: ignore

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from lograder.exception import DeveloperException
from lograder.process.cli_args import (
    CLI_ARG_MISSING,
    CLIArgs,
    CLIFlag,
    CLIKVOption,
    CLIMultiOption,
    CLIOption,
    CLIPresenceFlag,
    validate_single_specification,
)


def test_cli_arg_missing_is_singleton() -> None:
    assert CLI_ARG_MISSING() is CLI_ARG_MISSING()


def test_clioption_requires_emit_or_emitter() -> None:
    with pytest.raises(
        DeveloperException, match="either an emit sequence or an emitter"
    ):
        CLIOption(emit=None, emitter=None)


def test_validate_single_specification_accepts_exactly_one_non_none() -> None:
    validate_single_specification("X", a=1, b=None)
    validate_single_specification("X", a=None, b=1)
    with pytest.raises(DeveloperException):
        validate_single_specification("X", a=None, b=None)  # noqa: B018


def test_validate_single_specification_raises_when_all_none() -> None:
    with pytest.raises(DeveloperException, match="cannot all be `None`"):
        validate_single_specification("X", a=None, b=None, c=None)


class BasicArgs(CLIArgs):
    value: str = CLIOption(emit=["--value", "{}"])


def test_clioption_emit_metadata_is_attached() -> None:
    field = BasicArgs.model_fields["value"]
    assert field.json_schema_extra is not None
    assert "cli" in field.json_schema_extra
    cli = field.json_schema_extra["cli"]
    assert cli["emit"] == ["--value", "{}"]
    assert cli["emitter"] is None


def test_get_cli_schema_returns_transformer_for_cli_fields_only() -> None:
    class MixedArgs(CLIArgs):
        a: str = CLIOption(emit=["--a", "{}"])
        b: int = 3

    schema = MixedArgs.get_cli_schema()
    assert set(schema) == {"a"}


def test_cliargs_emit_simple_option() -> None:
    args = BasicArgs(value="hello")
    assert args.emit() == ["--value", "hello"]


def test_cliargs_emit_omits_cli_arg_missing() -> None:
    class MissingArgs(CLIArgs):
        maybe: str | CLI_ARG_MISSING = CLIOption(
            default=CLI_ARG_MISSING(), emit=["--x", "{}"]
        )

    args = MissingArgs()
    assert args.emit() == []


def test_cliargs_emit_with_custom_emitter() -> None:
    class EmitArgs(CLIArgs):
        value: int = CLIOption(emitter=lambda v: ["-n", str(v * 2)])

    args = EmitArgs(value=4)
    assert args.emit() == ["-n", "8"]


def test_climultioption_default_sequence_behavior() -> None:
    class MultiArgs(CLIArgs):
        items: list[int] = CLIMultiOption()

    args = MultiArgs(items=[1, 2, 3])
    assert args.emit() == ["1", "2", "3"]


def test_climultioption_token_emit_prefixes_each_item() -> None:
    class MultiArgs(CLIArgs):
        include_dirs: list[str] = CLIMultiOption(default=(), token_emit=["-I{}"])

    args = MultiArgs(include_dirs=["a", "b"])
    assert args.emit() == ["-Ia", "-Ib"]


def test_climultioption_sequence_emit_wraps_sequence() -> None:
    class MultiArgs(CLIArgs):
        values: list[str] = CLIMultiOption(
            sequence_emit=["--begin", ..., "--end"],
            token_emit=["{}"],
        )

    args = MultiArgs(values=["x", "y"])
    assert args.emit() == ["--begin", "x", "y", "--end"]


def test_climultioption_supports_sequence_emitter() -> None:
    class MultiArgs(CLIArgs):
        values: list[int] = CLIMultiOption(
            sequence_emitter=lambda xs: ["--count", str(len(list(xs))), ...],
            token_emit=["{}"],
        )

    args = MultiArgs(values=[10, 20])
    assert args.emit() == ["--count", "2", "10", "20"]


def test_climultioption_supports_token_emitter() -> None:
    class MultiArgs(CLIArgs):
        values: list[int] = CLIMultiOption(
            token_emit=None,
            token_emitter=lambda x: ["--v", str(x)],
        )

    args = MultiArgs(values=[1, 2])
    assert args.emit() == ["--v", "1", "--v", "2"]


def test_clikvoption_default_behavior() -> None:
    class KVArgs(CLIArgs):
        defines: dict[str, str] = CLIKVOption()

    args = KVArgs(defines={"A": "1", "B": "2"})
    assert args.emit() == ["A=1", "B=2"]


def test_clikvoption_token_emit_custom_format() -> None:
    class KVArgs(CLIArgs):
        defines: dict[str, str] = CLIKVOption(token_emit=["-D{key}={value}"])

    args = KVArgs(defines={"DEBUG": "1"})
    assert args.emit() == ["-DDEBUG=1"]


def test_clikvoption_token_emitter() -> None:
    class KVArgs(CLIArgs):
        defines: dict[str, str] = CLIKVOption(
            token_emit=None,
            token_emitter=lambda k, v: ["--define", f"{k}:{v}"],
        )

    args = KVArgs(defines={"MODE": "fast"})
    assert args.emit() == ["--define", "MODE:fast"]


def test_clikvoption_sequence_emit_with_ellipsis() -> None:
    class KVArgs(CLIArgs):
        defines: dict[str, str] = CLIKVOption(
            sequence_emit=["--defs", ..., "--done"],
            token_emit=["{key}={value}"],
        )

    args = KVArgs(defines={"A": "1", "B": "2"})
    assert args.emit() == ["--defs", "A=1", "B=2", "--done"]


def test_clipresenceflag_emits_when_true_and_present_when_true() -> None:
    class FlagArgs(CLIArgs):
        verbose: bool = CLIPresenceFlag(["-v"], default=False)

    assert FlagArgs(verbose=True).emit() == ["-v"]
    assert FlagArgs(verbose=False).emit() == []


def test_clipresenceflag_emits_when_false_and_present_when_false() -> None:
    class FlagArgs(CLIArgs):
        quiet_disabled: bool = CLIPresenceFlag(
            ["--no-quiet"], default=True, present_when=False
        )

    assert FlagArgs(quiet_disabled=False).emit() == ["--no-quiet"]
    assert FlagArgs(quiet_disabled=True).emit() == []


def test_cliflag_emits_true_branch() -> None:
    class FlagArgs(CLIArgs):
        toggle: bool = CLIFlag(["--yes"], ["--no"], default=True)

    assert FlagArgs(toggle=True).emit() == ["--yes"]


def test_cliflag_emits_false_branch() -> None:
    class FlagArgs(CLIArgs):
        toggle: bool = CLIFlag(["--yes"], ["--no"], default=False)

    assert FlagArgs(toggle=False).emit() == ["--no"]


def test_cliflag_non_bool_value_emits_nothing() -> None:
    class WeirdArgs(CLIArgs):
        toggle: Any = CLIFlag(["--yes"], ["--no"], default=None)

    assert WeirdArgs(toggle=None).emit() == []


def test_emit_preserves_field_definition_order() -> None:
    class OrderedArgs(CLIArgs):
        a: str = CLIOption(emit=["--a", "{}"])
        b: str = CLIOption(emit=["--b", "{}"])
        c: bool = CLIPresenceFlag(["-c"], default=False)

    args = OrderedArgs(a="x", b="y", c=True)
    assert args.emit() == ["--a", "x", "--b", "y", "-c"]


def test_emit_empty_from_no_cli_fields() -> None:
    class NoCLIArgs(CLIArgs):
        x: int = 1
        y: str = "abc"

    assert NoCLIArgs().emit() == []
