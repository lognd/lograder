from __future__ import annotations

import os

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.process.executable import ExecutableData, InstallWarning
from lograder.process.os_helpers import command_to_str


def _truncate(text: str, limit: int = 2000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... ({len(text) - limit} chars truncated)"


def _decode(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")


@register_layout("install-warning")
class InstallWarningLayout(Layout[InstallWarning]):
    @classmethod
    def to_simple(cls, data: InstallWarning) -> str:
        return (
            f"[WARN] `{data.calling_object}` (`{data.command[0]}`) not found."
            f" Attempting auto-install as fallback - this may hurt performance."
        )

    @classmethod
    def to_ansi(cls, data: InstallWarning) -> str:
        return (
            f"{S.BRIGHT}{F.YELLOW}[WARN]{F.RESET}{S.RESET_ALL}"
            f" `{F.CYAN}{data.calling_object}{F.RESET}`"
            f" (`{F.CYAN}{data.command[0]}{F.RESET}`) not found.\n"
            f"  Attempting auto-install as fallback"
            f" - {F.YELLOW}this may hurt performance{F.RESET}."
        )


@register_layout("executable-data")
class ExecutableDataLayout(Layout[ExecutableData]):
    @classmethod
    def to_simple(cls, data: ExecutableData) -> str:
        cmd = command_to_str(data.output.command)
        rc = data.output.return_code
        parts = [f"< EXEC > `{cmd}` -> exit {rc}\n"]
        if data.input.env and data.input.env != os.environ:
            env_str = ", ".join(f"{k}={v}" for k, v in data.input.env.items())
            parts.append(f"env: {env_str}\n")
        if data.input.stdin_bytes:
            parts.append(f"stdin: {repr(_decode(data.input.stdin_bytes))}\n")
        if data.output.stdout_bytes:
            parts.append(f"stdout:\n{_truncate(_decode(data.output.stdout_bytes))}\n")
        if data.output.stderr_bytes:
            parts.append(f"stderr:\n{_truncate(_decode(data.output.stderr_bytes))}\n")
        return "".join(parts)

    @classmethod
    def to_ansi(cls, data: ExecutableData) -> str:
        cmd = command_to_str(data.output.command)
        rc = data.output.return_code
        rc_color = F.GREEN if rc == 0 else F.RED
        parts = [
            f"{S.BRIGHT}< {F.CYAN}EXEC{F.RESET} >{S.RESET_ALL}"
            f" `{F.CYAN}{cmd}{F.RESET}` -> exit {rc_color}{rc}{F.RESET}\n"
        ]

        if data.input.env and data.input.env != os.environ:
            if data.input.hide_input:
                parts.append(f"  {F.YELLOW}env: (hidden){F.RESET}\n")
            else:
                env_lines = "\n".join(
                    f"  {F.YELLOW}{k}{F.RESET}={v}" for k, v in data.input.env.items()
                )
                parts.append(f"env:\n{env_lines}\n")

        if data.input.hide_input:
            parts.append(f"  stdin: {F.YELLOW}(hidden){F.RESET}\n")
        elif data.input.stdin_bytes:
            parts.append(f"stdin:\n{_truncate(_decode(data.input.stdin_bytes))}\n")

        if data.input.hide_output:
            parts.append(f"  stdout: {F.YELLOW}(hidden){F.RESET}\n")
            parts.append(f"  stderr: {F.YELLOW}(hidden){F.RESET}\n")
        else:
            if data.output.stdout_bytes:
                parts.append(
                    f"stdout:\n{_truncate(_decode(data.output.stdout_bytes))}\n"
                )
            if data.output.stderr_bytes:
                parts.append(
                    f"stderr:\n{_truncate(_decode(data.output.stderr_bytes))}\n"
                )

        return "".join(parts)
