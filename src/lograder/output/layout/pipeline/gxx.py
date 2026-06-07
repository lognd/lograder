from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.build.gxx import GXXBuildError, GXXBuildOutput


def _truncate(text: str, limit: int = 800) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... ({len(text) - limit} chars truncated)"


def _sources_str(sources: list[str]) -> str:
    return ", ".join(sources) if sources else "(none)"


@register_layout("gxx-build-output")
class GXXBuildOutputLayout(Layout[GXXBuildOutput]):
    @classmethod
    def to_ansi(cls, data: GXXBuildOutput) -> str:
        lines = [
            f"{S.BRIGHT}< {F.GREEN}G++ BUILD{F.RESET} >{S.RESET_ALL}"
            f" [{F.CYAN}{_sources_str(data.sources)}{F.RESET}"
            f" -> {F.CYAN}{data.output}{F.RESET}]",
        ]
        if data.stderr.strip():
            lines.append(
                f"{S.DIM}stderr:{S.RESET_ALL}\n{_truncate(data.stderr.rstrip())}"
            )
        return "\n".join(lines)

    @classmethod
    def to_simple(cls, data: GXXBuildOutput) -> str:
        return f"[BUILD] {_sources_str(data.sources)} -> {data.output}"


@register_layout("gxx-build-error")
class GXXBuildErrorLayout(Layout[GXXBuildError]):
    @classmethod
    def to_ansi(cls, data: GXXBuildError) -> str:
        lines = [
            f"{S.BRIGHT}< {F.RED}G++ BUILD ERROR{F.RESET} >{S.RESET_ALL}"
            f" [{F.CYAN}{_sources_str(data.sources)}{F.RESET}]",
            f"  {F.RED}{data.message}{F.RESET}",
        ]
        if data.stderr and data.stderr.strip():
            lines.append(
                f"{S.DIM}stderr:{S.RESET_ALL}\n{_truncate(data.stderr.rstrip())}"
            )
        if data.stdout and data.stdout.strip():
            lines.append(
                f"{S.DIM}stdout:{S.RESET_ALL}\n{_truncate(data.stdout.rstrip())}"
            )
        return "\n".join(lines)

    @classmethod
    def to_simple(cls, data: GXXBuildError) -> str:
        parts = [f"[BUILD ERROR] {_sources_str(data.sources)}: {data.message}"]
        if data.stderr and data.stderr.strip():
            parts.append(_truncate(data.stderr.rstrip()))
        return "\n".join(parts)
