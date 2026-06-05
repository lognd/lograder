from __future__ import annotations

from pathlib import Path

from lograder.process.cli_args import (
    CLI_ARG_MISSING,
    CLIArgs,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import TypedExecutable, register_typed_executable


class CTestArgs(CLIArgs):
    # ── Test selection ─────────────────────────────────────────────────────────
    test_regex: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-R", "{}"],
    )
    exclude_regex: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-E", "{}"],
    )
    label_regex: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-L", "{}"],
    )
    exclude_label_regex: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-LE", "{}"],
    )
    # Run only the tests specified by index/range (e.g. "2,4,6,8")
    tests_index: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-I", "{}"],
    )
    rerun_failed: bool = CLIPresenceFlag(["--rerun-failed"], default=False)
    run_disabled: bool = CLIPresenceFlag(["--run-disabled"], default=False)

    # ── Execution ──────────────────────────────────────────────────────────────
    parallel: int | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-j", "{}"],
    )
    timeout: float | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["--timeout", "{}"],
    )
    stop_on_failure: bool = CLIPresenceFlag(["--stop-on-failure"], default=False)
    schedule_random: bool = CLIPresenceFlag(["--schedule-random"], default=False)
    repeat: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["--repeat", "{}"],
    )

    # ── Build/configuration ────────────────────────────────────────────────────
    build_config: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["-C", "{}"],
    )
    # Where to find CTestTestfile.cmake (the build directory)
    test_dir: Path | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["--test-dir", "{}"],
    )
    # Override individual test env (KEY=VALUE, repeatable)
    overwrite: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["--overwrite", "{}"],
    )

    # ── Output ─────────────────────────────────────────────────────────────────
    output_junit: Path | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(),
        emit=["--output-junit", "{}"],
    )
    output_on_failure: bool = CLIPresenceFlag(["--output-on-failure"], default=False)
    no_compress_output: bool = CLIPresenceFlag(["--no-compress-output"], default=False)
    verbose: bool = CLIPresenceFlag(["-V"], default=False)
    extra_verbose: bool = CLIPresenceFlag(["-VV"], default=False)
    quiet: bool = CLIPresenceFlag(["-Q"], default=False)

    # ── Informational ──────────────────────────────────────────────────────────
    show_only: bool = CLIPresenceFlag(["-N"], default=False)
    print_labels: bool = CLIPresenceFlag(["--print-labels"], default=False)


@register_typed_executable(["ctest"])
class CTestExecutable(TypedExecutable[CTestArgs]):
    pass
