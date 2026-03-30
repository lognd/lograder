# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.registry.ar import ArArgs, ArExecutable, ArOperation


def test_ar_basic_replace() -> None:
    args = ArArgs(
        operation=ArOperation.REPLACE,
        create=True,
        index=True,
        archive=Path("lib.a"),
        files=[Path("a.o"), Path("b.o")],
    )

    assert args.emit() == ["rcs", "lib.a", "a.o", "b.o"]


def test_ar_extract_verbose() -> None:
    args = ArArgs(
        operation=ArOperation.EXTRACT,
        verbose=True,
        archive=Path("lib.a"),
        files=[Path("a.o")],
    )

    assert args.emit() == ["xv", "lib.a", "a.o"]


def test_ar_table_no_files() -> None:
    args = ArArgs(
        operation=ArOperation.TABLE,
        archive=Path("lib.a"),
    )

    assert args.emit() == ["t", "lib.a"]


def test_ar_insert_after_requires_position_member() -> None:
    with pytest.raises(ValidationError):
        ArArgs(
            operation=ArOperation.REPLACE,
            insert_after=True,
            archive=Path("lib.a"),
            files=[Path("a.o")],
        )


def test_ar_insert_after_valid() -> None:
    args = ArArgs(
        operation=ArOperation.REPLACE,
        insert_after=True,
        position_member=Path("ref.o"),
        archive=Path("lib.a"),
        files=[Path("a.o")],
    )

    assert args.emit() == ["ra", "lib.a", "ref.o", "a.o"]


def test_ar_mutually_exclusive_insert_flags() -> None:
    with pytest.raises(ValidationError):
        ArArgs(
            operation=ArOperation.REPLACE,
            insert_after=True,
            insert_before=True,
            position_member=Path("ref.o"),
            archive=Path("lib.a"),
        )


def test_ar_raw_modifiers_passthrough() -> None:
    args = ArArgs(
        operation=ArOperation.REPLACE,
        raw_modifiers="D",
        archive=Path("lib.a"),
        files=[Path("a.o")],
    )

    assert args.emit() == ["rD", "lib.a", "a.o"]


def test_ar_emit_string_contains_expected() -> None:
    args = ArArgs(
        operation=ArOperation.REPLACE,
        create=True,
        index=True,
        archive=Path("lib.a"),
        files=[Path("a.o")],
    )

    assert "rcs lib.a a.o" in " ".join(args.emit())


def test_ar_rejects_blank_archive() -> None:
    with pytest.raises(ValidationError):
        ArArgs(
            operation=ArOperation.REPLACE,
            archive="   ",
        )


def test_ar_executable_registered() -> None:
    assert ArExecutable.executable is not None
    assert ArExecutable.executable.command == ["ar"]
