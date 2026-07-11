from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from lograder.process.registry.gas import GasArgs, GasExecutable


def test_basic_assembly(tmp_path: Path) -> None:
    src = tmp_path / "a.s"
    src.write_text("")

    args = GasArgs(input=[src])

    assert args.emit() == [str(src)]


def test_output_and_arch(tmp_path: Path) -> None:
    src = tmp_path / "a.s"
    src.write_text("")

    args = GasArgs(
        input=[src],
        output=tmp_path / "a.o",
        architecture="x86-64",
    )

    emitted = args.emit()
    assert str(src) in emitted
    assert "-o" in emitted
    assert str(tmp_path / "a.o") in emitted
    assert "-march=x86-64" in emitted


def test_debug_and_warnings(tmp_path: Path) -> None:
    src = tmp_path / "a.s"
    src.write_text("")

    args = GasArgs(
        input=[src],
        debug=True,
        warnings=True,
        fatal_warnings=True,
    )

    emitted = args.emit()
    assert str(src) in emitted
    assert "-g" in emitted
    assert "--warn" in emitted
    assert "--fatal-warnings" in emitted


def test_include_and_defines(tmp_path: Path) -> None:
    src = tmp_path / "a.s"
    src.write_text("")

    include_dir = tmp_path / "include"
    include_dir.mkdir()

    args = GasArgs(
        input=[src],
        include_dirs=[include_dir],
        defines={"FOO": 1, "BAR": None},
    )

    emitted = args.emit()
    assert str(src) in emitted
    assert f"-I{include_dir}" in emitted
    assert "-DFOO=1" in emitted
    assert "-DBAR" in emitted


def test_listing(tmp_path: Path) -> None:
    src = tmp_path / "a.s"
    src.write_text("")

    listing = tmp_path / "out.lst"

    args = GasArgs(
        input=[src],
        listing=listing,
    )

    emitted = args.emit()
    assert str(src) in emitted
    assert f"-al={listing}" in emitted


def test_add_opts_passthrough(tmp_path: Path) -> None:
    src = tmp_path / "a.s"
    src.write_text("")

    args = GasArgs(
        input=[src],
        add_opts=["--gdwarf-5"],
    )

    emitted = args.emit()
    assert str(src) in emitted
    assert "--gdwarf-5" in emitted


def test_reject_empty_input() -> None:
    with pytest.raises(ValidationError):
        GasArgs(input=[])


def test_reject_blank_input_string() -> None:
    with pytest.raises(ValidationError):
        GasArgs(input=["   "])


def test_reject_nonexistent_input_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.s"

    with pytest.raises(ValidationError):
        GasArgs(input=[missing])


def test_registered() -> None:
    assert GasExecutable.executable is not None
    assert GasExecutable.executable.command == ["as"]


# --- Real executable tests ---

import platform as _platform  # noqa: E402
import shutil as _shutil  # noqa: E402

_AS_AVAILABLE = bool(_shutil.which("as"))

# Minimal "return 0 from foo" assembly, one variant per host architecture --
# `as` is architecture-specific, so a single fixed source only assembles on the
# arch it was written for (the previous AArch64-only source failed on x86-64 CI
# runners). Select the matching source from the host's reported machine; when
# the arch is not one we have a snippet for, _HELLO_ASM is None and the real-
# assembly tests below skip.
_HELLO_ASM_BY_ARCH = {
    "x86_64": "    .text\n    .globl foo\nfoo:\n    xorl %eax, %eax\n    ret\n",
    "amd64": "    .text\n    .globl foo\nfoo:\n    xorl %eax, %eax\n    ret\n",
    "i386": "    .text\n    .globl foo\nfoo:\n    xorl %eax, %eax\n    ret\n",
    "i686": "    .text\n    .globl foo\nfoo:\n    xorl %eax, %eax\n    ret\n",
    "aarch64": "    .text\n    .globl foo\nfoo:\n    mov x0, #0\n    ret\n",
    "arm64": "    .text\n    .globl foo\nfoo:\n    mov x0, #0\n    ret\n",
    "armv7l": "    .text\n    .globl foo\nfoo:\n    mov r0, #0\n    bx lr\n",
    "armv6l": "    .text\n    .globl foo\nfoo:\n    mov r0, #0\n    bx lr\n",
    "riscv64": "    .text\n    .globl foo\nfoo:\n    li a0, 0\n    ret\n",
}
_HELLO_ASM = _HELLO_ASM_BY_ARCH.get(_platform.machine().lower())
_AS_USABLE = _AS_AVAILABLE and _HELLO_ASM is not None


@pytest.mark.skipif(
    not _AS_USABLE, reason="as (gas) unavailable or no asm snippet for this arch"
)
def test_gas_real_assembles_x86_source(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions

    src = tmp_path / "main.s"
    src.write_text(_HELLO_ASM, encoding="utf-8")
    obj = tmp_path / "main.o"

    exe = GasExecutable()
    args = GasArgs(input=[src], output=obj)
    result = exe(args, options=ExecutableOptions(cwd=tmp_path))
    assert result.is_ok
    assert result.danger_ok.return_code == 0
    assert obj.exists()


@pytest.mark.skipif(
    not _AS_USABLE, reason="as (gas) unavailable or no asm snippet for this arch"
)
def test_gas_real_debug_info_flag(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions

    src = tmp_path / "foo.s"
    src.write_text(_HELLO_ASM, encoding="utf-8")
    obj = tmp_path / "foo.o"

    exe = GasExecutable()
    args = GasArgs(input=[src], output=obj, debug=True)
    result = exe(args, options=ExecutableOptions(cwd=tmp_path))
    assert result.is_ok
    assert result.danger_ok.return_code == 0
    assert obj.exists()
