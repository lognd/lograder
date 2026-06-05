from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.build.bash_script import (
    BashScriptBuildError,
    BashScriptBuildOutput,
)


def _truncate(text: str, limit: int = 800) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... ({len(text) - limit} chars truncated)"


@register_layout("bash-script-build-output")
class BashScriptBuildOutputLayout(Layout[BashScriptBuildOutput]):
    @classmethod
    def to_ansi(cls, data: BashScriptBuildOutput) -> str:
        lines = [
            f"{S.BRIGHT}< {F.CYAN}BASH SCRIPT BUILD{F.RESET} >{S.RESET_ALL}"
            f" [{F.CYAN}{data.script}{F.RESET}]",
            f"{F.GREEN}Script exited {data.return_code}.{F.RESET}",
        ]
        if data.stdout.strip():
            lines.append(
                f"{S.DIM}stdout:{S.RESET_ALL}\n{_truncate(data.stdout.rstrip())}"
            )
        if data.stderr.strip():
            lines.append(
                f"{S.DIM}stderr:{S.RESET_ALL}\n{_truncate(data.stderr.rstrip())}"
            )
        return "\n".join(lines)

    @classmethod
    def to_simple(cls, data: BashScriptBuildOutput) -> str:
        return f"[BUILD] {data.script} exited {data.return_code}."


@register_layout("bash-script-build-error")
class BashScriptBuildErrorLayout(Layout[BashScriptBuildError]):
    @classmethod
    def to_ansi(cls, data: BashScriptBuildError) -> str:
        lines = [
            f"{S.BRIGHT}< {F.RED}BASH SCRIPT BUILD ERROR{F.RESET} >{S.RESET_ALL}"
            f" [{F.CYAN}{data.script}{F.RESET}]",
            f"  {data.message}",
        ]
        if data.stdout and data.stdout.strip():
            lines.append(
                f"{S.DIM}stdout:{S.RESET_ALL}\n{_truncate(data.stdout.rstrip())}"
            )
        if data.stderr and data.stderr.strip():
            lines.append(
                f"{S.DIM}stderr:{S.RESET_ALL}\n{_truncate(data.stderr.rstrip())}"
            )
        return "\n".join(lines)

    @classmethod
    def to_simple(cls, data: BashScriptBuildError) -> str:
        return f"[BUILD ERROR] {data.script}: {data.message}"
