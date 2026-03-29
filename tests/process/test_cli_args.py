# type: ignore

from __future__ import annotations

from typing import Any

import pytest

from lograder.exception import DeveloperException
from lograder.process.cli_args import (
    CLI_ARG_MISSING,
    POSITION_AGNOSTIC,
    CLIArgs,
    CLIFlag,
    CLIKVOption,
    CLIMultiOption,
    CLIOption,
    CLIPresenceFlag,
    _is_position_agnostic,
    _order_emitted_arguments,
    _validate_declared_positions,
    validate_single_specification,
)


def test_cli_arg_missing_is_singleton() -> None:
    assert CLI_ARG_MISSING() is CLI_ARG_MISSING()


def test_position_agnostic_is_singleton() -> None:
    assert POSITION_AGNOSTIC() is POSITION_AGNOSTIC()


def test_is_position_agnostic_true_for_singleton_instance() -> None:
    assert _is_position_agnostic(POSITION_AGNOSTIC()) is True


def test_is_position_agnostic_false_for_int_position() -> None:
    assert _is_position_agnostic(0) is False
    assert _is_position_agnostic(1) is False
    assert _is_position_agnostic(-1) is False


def test_clioption_requires_emit_or_emitter() -> None:
    with pytest.raises(
        DeveloperException, match="either an emit sequence or an emitter"
    ):
        CLIOption(emit=None, emitter=None)


def test_validate_single_specification_accepts_exactly_one_non_none() -> None:
    validate_single_specification("X", a=1, b=None)
    validate_single_specification("X", a=None, b=1)


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
    assert _is_position_agnostic(cli["position"])


def test_get_cli_schema_returns_transformer_for_cli_fields_only() -> None:
    class MixedArgs(CLIArgs):
        a: str = CLIOption(emit=["--a", "{}"])
        b: int = 3

    schema = MixedArgs.get_cli_schema()
    assert set(schema) == {"a"}


def test_get_cli_schema_returns_position_and_transformer() -> None:
    class PosArgs(CLIArgs):
        a: str = CLIOption(emit=["--a", "{}"], position=0)

    schema = PosArgs.get_cli_schema()
    position, transformation = schema["a"]

    assert position == 0
    assert transformation("x") == ["--a", "x"]


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


def test_climultioption_preserves_position_metadata() -> None:
    class MultiArgs(CLIArgs):
        values: list[int] = CLIMultiOption(position=0)

    schema = MultiArgs.get_cli_schema()
    position, _ = schema["values"]
    assert position == 0


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


def test_clikvoption_preserves_position_metadata() -> None:
    class KVArgs(CLIArgs):
        defines: dict[str, str] = CLIKVOption(position=-1)

    schema = KVArgs.get_cli_schema()
    position, _ = schema["defines"]
    assert position == -1


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


def test_clipresenceflag_preserves_pos_position_metadata() -> None:
    class FlagArgs(CLIArgs):
        verbose: bool = CLIPresenceFlag(["-v"], default=False, position=0)

    schema = FlagArgs.get_cli_schema()
    position, _ = schema["verbose"]
    assert position == 0


def test_clipresenceflag_preserves_neg_position_metadata() -> None:
    class FlagArgs(CLIArgs):
        verbose: bool = CLIPresenceFlag(["-v"], default=False, position=-1)

    schema = FlagArgs.get_cli_schema()
    position, _ = schema["verbose"]
    assert position == -1


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


def test_cliflag_preserves_position_metadata() -> None:
    class FlagArgs(CLIArgs):
        toggle: bool = CLIFlag(["--yes"], ["--no"], default=False, position=-1)

    schema = FlagArgs.get_cli_schema()
    position, _ = schema["toggle"]
    assert position == -1


def test_emit_preserves_field_definition_order_when_all_agnostic() -> None:
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


def test_emit_skips_empty_emissions_before_positioning() -> None:
    class Args(CLIArgs):
        a: str = CLIOption(emit=["--a", "{}"], position=0)
        b: bool = CLIPresenceFlag(["-b"], default=False, position=1)
        c: str = CLIOption(emit=["--c", "{}"], position=-1)

    args = Args(a="x", b=False, c="z")
    assert args.emit() == ["--a", "x", "--c", "z"]


def test_position_zero_places_block_first() -> None:
    class Args(CLIArgs):
        a: str = CLIOption(emit=["A", "{}"])
        b: str = CLIOption(emit=["B", "{}"], position=0)

    args = Args(a="x", b="y")
    assert args.emit() == ["B", "y", "A", "x"]


def test_position_one_places_block_second() -> None:
    class Args(CLIArgs):
        a: str = CLIOption(emit=["A", "{}"], position=1)
        b: str = CLIOption(emit=["B", "{}"])
        c: str = CLIOption(emit=["C", "{}"])

    args = Args(a="x", b="y", c="z")
    assert args.emit() == ["B", "y", "A", "x", "C", "z"]


def test_negative_one_places_block_last() -> None:
    class Args(CLIArgs):
        a: str = CLIOption(emit=["A", "{}"])
        b: str = CLIOption(emit=["B", "{}"], position=-1)

    args = Args(a="x", b="y")
    assert args.emit() == ["A", "x", "B", "y"]


def test_negative_two_places_block_second_to_last() -> None:
    class Args(CLIArgs):
        a: str = CLIOption(emit=["A", "{}"])
        b: str = CLIOption(emit=["B", "{}"], position=-2)
        c: str = CLIOption(emit=["C", "{}"])

    args = Args(a="x", b="y", c="z")
    assert args.emit() == ["A", "x", "B", "y", "C", "z"]


def test_mixed_positive_negative_and_agnostic_positions() -> None:
    class Args(CLIArgs):
        first: str = CLIOption(emit=["FIRST", "{}"], position=0)
        middle: str = CLIOption(emit=["MID", "{}"])
        last: str = CLIOption(emit=["LAST", "{}"], position=-1)

    args = Args(first="a", middle="b", last="c")
    assert args.emit() == ["FIRST", "a", "MID", "b", "LAST", "c"]


def test_multiple_agnostic_blocks_fill_remaining_slots_in_definition_order() -> None:
    class Args(CLIArgs):
        first: str = CLIOption(emit=["FIRST", "{}"], position=0)
        a: str = CLIOption(emit=["A", "{}"])
        b: str = CLIOption(emit=["B", "{}"])
        last: str = CLIOption(emit=["LAST", "{}"], position=-1)

    args = Args(first="1", a="2", b="3", last="4")
    assert args.emit() == ["FIRST", "1", "A", "2", "B", "3", "LAST", "4"]


def test_positioning_operates_on_field_blocks_not_individual_tokens() -> None:
    class Args(CLIArgs):
        output: str = CLIOption(emit=["-o", "{}"], position=-1)
        source: str = CLIOption(emit=["{}"])

    args = Args(output="prog", source="main.c")
    assert args.emit() == ["main.c", "-o", "prog"]


def test_definition_time_positive_position_out_of_bounds_raises() -> None:
    with pytest.raises(DeveloperException, match="can never exist"):

        class BadArgs(CLIArgs):
            a: str = CLIOption(emit=["A", "{}"], position=2)
            b: str = CLIOption(emit=["B", "{}"])


def test_definition_time_negative_position_out_of_bounds_raises() -> None:
    with pytest.raises(DeveloperException, match="can never exist"):

        class BadArgs(CLIArgs):
            a: str = CLIOption(emit=["A", "{}"], position=-3)
            b: str = CLIOption(emit=["B", "{}"])


def test_definition_time_allows_overlap_that_is_only_instance_dependent() -> None:
    class Args(CLIArgs):
        first: str = CLIOption(emit=["FIRST", "{}"], position=0)
        second_to_last: str = CLIOption(emit=["SECOND_LAST", "{}"], position=-2)
        maybe: bool = CLIPresenceFlag(["--maybe"], default=False)

    schema = Args.get_cli_schema()
    assert set(schema) == {"first", "second_to_last", "maybe"}


def test_emit_time_overlap_between_positive_and_negative_positions_raises() -> None:
    class Args(CLIArgs):
        first: str = CLIOption(emit=["FIRST", "{}"], position=0)
        second_to_last: str = CLIOption(emit=["SECOND_LAST", "{}"], position=-2)
        maybe: bool = CLIPresenceFlag(["--maybe"], default=False)

    args = Args(first="a", second_to_last="b", maybe=False)

    with pytest.raises(DeveloperException, match="both resolved to CLI position `0`"):
        args.emit()


def test_emit_time_overlap_disappears_when_extra_block_emits() -> None:
    class Args(CLIArgs):
        first: str = CLIOption(emit=["FIRST", "{}"], position=0)
        second_to_last: str = CLIOption(emit=["SECOND_LAST", "{}"], position=-2)
        maybe: bool = CLIPresenceFlag(["--maybe"], default=False)

    args = Args(first="a", second_to_last="b", maybe=True)
    assert args.emit() == ["FIRST", "a", "SECOND_LAST", "b", "--maybe"]


def test_emit_time_negative_position_can_go_out_of_bounds_after_empty_blocks() -> None:
    class Args(CLIArgs):
        a: bool = CLIPresenceFlag(["-a"], default=False)
        b: str = CLIOption(emit=["B", "{}"], position=-2)

    args = Args(a=False, b="x")

    with pytest.raises(DeveloperException, match="only emitted 1 argument block"):
        args.emit()


def test_emit_time_positive_position_can_go_out_of_bounds_after_empty_blocks() -> None:
    class Args(CLIArgs):
        a: bool = CLIPresenceFlag(["-a"], default=False)
        b: str = CLIOption(emit=["B", "{}"], position=1)

    args = Args(a=False, b="x")

    with pytest.raises(DeveloperException, match="only emitted 1 argument block"):
        args.emit()


def test_emit_rejects_string_output_from_emitter() -> None:
    class Args(CLIArgs):
        bad: int = CLIOption(emitter=lambda v: "oops")  # type: ignore[arg-type]

    args = Args(bad=1)

    with pytest.raises(DeveloperException, match="was found to be a `str`"):
        args.emit()


def test_emit_rejects_empty_string_token_in_output() -> None:
    class Args(CLIArgs):
        bad: int = CLIOption(emitter=lambda v: ["--x", ""])  # type: ignore[arg-type]

    args = Args(bad=1)

    with pytest.raises(DeveloperException, match="empty string token"):
        args.emit()


def test_validate_declared_positions_accepts_all_agnostic() -> None:
    schema = {
        "a": (POSITION_AGNOSTIC(), lambda v: ["a"]),
        "b": (POSITION_AGNOSTIC(), lambda v: ["b"]),
    }
    _validate_declared_positions("X", schema)


def test_validate_declared_positions_rejects_impossible_positive_position() -> None:
    schema = {
        "a": (2, lambda v: ["a"]),
        "b": (POSITION_AGNOSTIC(), lambda v: ["b"]),
    }

    with pytest.raises(DeveloperException, match="can never exist"):
        _validate_declared_positions("X", schema)


def test_validate_declared_positions_rejects_impossible_negative_position() -> None:
    schema = {
        "a": (-3, lambda v: ["a"]),
        "b": (POSITION_AGNOSTIC(), lambda v: ["b"]),
    }

    with pytest.raises(DeveloperException, match="can never exist"):
        _validate_declared_positions("X", schema)


def test_order_emitted_arguments_empty_returns_empty() -> None:
    assert _order_emitted_arguments("X", []) == []


def test_order_emitted_arguments_all_agnostic_preserves_order() -> None:
    emitted = [
        ("a", POSITION_AGNOSTIC(), ["A", "1"]),
        ("b", POSITION_AGNOSTIC(), ["B", "2"]),
    ]
    assert _order_emitted_arguments("X", emitted) == ["A", "1", "B", "2"]


def test_order_emitted_arguments_honors_explicit_positions() -> None:
    emitted = [
        ("a", POSITION_AGNOSTIC(), ["A", "1"]),
        ("b", 0, ["B", "2"]),
        ("c", -1, ["C", "3"]),
    ]
    assert _order_emitted_arguments("X", emitted) == ["B", "2", "A", "1", "C", "3"]


def test_order_emitted_arguments_rejects_resolved_collision() -> None:
    emitted = [
        ("a", 0, ["A", "1"]),
        ("b", -2, ["B", "2"]),
    ]

    with pytest.raises(DeveloperException, match="both resolved to CLI position `0`"):
        _order_emitted_arguments("X", emitted)


def test_order_emitted_arguments_rejects_instance_out_of_bounds_positive() -> None:
    emitted = [
        ("a", 1, ["A", "1"]),
    ]

    with pytest.raises(DeveloperException, match="only emitted 1 argument block"):
        _order_emitted_arguments("X", emitted)


def test_order_emitted_arguments_rejects_instance_out_of_bounds_negative() -> None:
    emitted = [
        ("a", -2, ["A", "1"]),
    ]

    with pytest.raises(DeveloperException, match="only emitted 1 argument block"):
        _order_emitted_arguments("X", emitted)
