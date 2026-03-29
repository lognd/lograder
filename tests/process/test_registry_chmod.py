# type: ignore

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.registry.chmod import CHModArgs, CHModExecutable


def test_chmod_args_octal_mode_emit() -> None:
    args = CHModArgs(
        mode="755",
        paths=[Path("script.sh")],
    )

    toks = ["755", "script.sh"]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    assert args.emit() == ["755", "script.sh"]


def test_chmod_args_symbolic_mode_emit() -> None:
    args = CHModArgs(
        mode="u+rwx,go+rx",
        paths=[Path("prog"), Path("tool")],
    )

    toks = ["u+rwx,go+rx", "prog", "tool"]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    assert args.emit() == ["u+rwx,go+rx", "prog", "tool"]


def test_chmod_args_full_emit() -> None:
    args = CHModArgs(
        mode="755",
        recursive=True,
        force=True,
        verbose=True,
        no_dereference=True,
        paths=[Path("scripts"), Path("bin/tool.sh")],
    )

    toks = ["755", "-R", "-f", "-v", "-h", "scripts", "bin/tool.sh"]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    emitted = args.emit()
    assert "755" in emitted
    assert "-R" in emitted
    assert "-f" in emitted
    assert "-v" in emitted
    assert "-h" in emitted
    assert "scripts" in emitted
    assert "bin/tool.sh" in emitted

    # mode should come before trailing operands
    assert emitted[0] == "755"
    assert emitted[-2:] == ["scripts", "bin/tool.sh"]


def test_chmod_args_reference_emit() -> None:
    args = CHModArgs(
        reference=Path("template.sh"),
        paths=[Path("generated.sh")],
    )

    toks = ["--reference=template.sh", "generated.sh"]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    assert args.emit() == ["--reference=template.sh", "generated.sh"]


def test_chmod_args_reference_with_flags_emit() -> None:
    args = CHModArgs(
        reference=Path("template.sh"),
        recursive=True,
        changes=True,
        paths=[Path("out.sh"), Path("more/out2.sh")],
    )

    toks = [
        "--reference=template.sh",
        "-R",
        "-c",
        "out.sh",
        "more/out2.sh",
    ]
    args_str = " ".join(args.emit())
    for tok in toks:
        assert tok in args_str

    emitted = args.emit()
    assert "--reference=template.sh" in emitted
    assert "-R" in emitted
    assert "-c" in emitted
    assert emitted[-2:] == ["out.sh", "more/out2.sh"]


def test_chmod_registered_command() -> None:
    assert CHModExecutable.executable is not None
    assert CHModExecutable.executable.command == ["chmod"]


def test_chmod_requires_exactly_one_of_mode_or_reference_neither() -> None:
    with pytest.raises(ValidationError):
        CHModArgs(
            paths=[Path("file.txt")],
        )


def test_chmod_requires_exactly_one_of_mode_or_reference_both() -> None:
    with pytest.raises(ValidationError):
        CHModArgs(
            mode="755",
            reference=Path("template.sh"),
            paths=[Path("file.txt")],
        )


def test_chmod_requires_at_least_one_path() -> None:
    with pytest.raises(ValidationError):
        CHModArgs(
            mode="755",
            paths=[],
        )


def test_chmod_rejects_blank_mode() -> None:
    with pytest.raises(ValidationError):
        CHModArgs(
            mode="   ",
            paths=[Path("file.txt")],
        )


def test_chmod_rejects_bad_numeric_mode() -> None:
    with pytest.raises(ValidationError):
        CHModArgs(
            mode="999",
            paths=[Path("file.txt")],
        )


def test_chmod_rejects_bad_symbolic_mode() -> None:
    with pytest.raises(ValidationError):
        CHModArgs(
            mode="this-is-not-valid",
            paths=[Path("file.txt")],
        )


def test_chmod_rejects_invalid_symbolic_clause() -> None:
    with pytest.raises(ValidationError):
        CHModArgs(
            mode="u+rwx,go",
            paths=[Path("file.txt")],
        )


def test_chmod_rejects_reference_directory(tmp_path: Path) -> None:
    ref_dir = tmp_path / "refdir"
    ref_dir.mkdir()

    with pytest.raises(ValidationError):
        CHModArgs(
            reference=ref_dir,
            paths=[tmp_path / "target.txt"],
        )


def test_chmod_rejects_verbose_and_changes_together() -> None:
    with pytest.raises(ValidationError):
        CHModArgs(
            mode="755",
            verbose=True,
            changes=True,
            paths=[Path("file.txt")],
        )


def test_chmod_accepts_common_symbolic_modes() -> None:
    valid_modes = [
        "u+x",
        "a+r",
        "go-w",
        "u=rw",
        "u=rw,go=r",
        "a+X",
        "u+s",
        "g-s",
    ]

    for mode in valid_modes:
        args = CHModArgs(mode=mode, paths=[Path("file.txt")])
        assert args.mode == mode


def test_chmod_accepts_common_octal_modes() -> None:
    valid_modes = ["644", "755", "4755", "0644"]

    for mode in valid_modes:
        args = CHModArgs(mode=mode, paths=[Path("file.txt")])
        assert args.mode == mode
