from __future__ import annotations

from lograder.process.cli_args import (
    CLI_ARG_MISSING,
    CLIArgs,
    CLIOption,
    CLIPresenceFlag,
)
from lograder.process.executable import TypedExecutable, register_typed_executable


class GTestArgs(CLIArgs):
    """Arguments for a Google Test binary.

    Pass to ``GTestTest`` via ``base_args``; ``--gtest_output`` is always
    overridden internally to capture JUnit XML.
    """

    # -- Output (managed internally by GTestTest) -------------------------------
    # Value: "xml", "xml:<path>", "json", "json:<path>"
    gtest_output: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--gtest_output={}"]
    )

    # -- Test selection ---------------------------------------------------------
    # Glob pattern: "SuiteName.TestName", "Suite*", "-Suite.Test" to exclude
    gtest_filter: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--gtest_filter={}"]
    )
    gtest_also_run_disabled_tests: bool = CLIPresenceFlag(
        ["--gtest_also_run_disabled_tests"], default=False
    )

    # -- Execution --------------------------------------------------------------
    gtest_repeat: int | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--gtest_repeat={}"]
    )
    gtest_shuffle: bool = CLIPresenceFlag(["--gtest_shuffle"], default=False)
    gtest_random_seed: int | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--gtest_random_seed={}"]
    )
    gtest_recreate_environments_when_repeating: bool = CLIPresenceFlag(
        ["--gtest_recreate_environments_when_repeating"], default=False
    )
    gtest_fail_fast: bool = CLIPresenceFlag(["--gtest_fail_fast"], default=False)

    # -- Output verbosity -------------------------------------------------------
    # Values: "yes", "no", "all", "short", "detailed"
    gtest_brief: bool = CLIPresenceFlag(["--gtest_brief=1"], default=False)
    gtest_print_time: bool = CLIPresenceFlag(["--gtest_print_time=1"], default=False)

    # -- Death test ------------------------------------------------------------
    # "fast", "safe", "threadsafe"
    gtest_death_test_style: str | CLI_ARG_MISSING = CLIOption(
        default=CLI_ARG_MISSING(), emit=["--gtest_death_test_style={}"]
    )

    # -- Informational ----------------------------------------------------------
    gtest_list_tests: bool = CLIPresenceFlag(["--gtest_list_tests"], default=False)


@register_typed_executable(["gtest"])
class GTestExecutable(TypedExecutable[GTestArgs]):
    """Placeholder executable; not used directly (GTestTest invokes FileArtifact.executable)."""

    pass
