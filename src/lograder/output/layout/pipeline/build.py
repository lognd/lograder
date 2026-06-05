from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.build.build import BuildOutput


def _build_summary(data: BuildOutput) -> str:
    if data.install_error is not None:
        return f"install error: {data.install_error.message}"
    if data.executable_output is not None:
        out = data.executable_output
        return f"exit {out.return_code} - {str(data.config_file.name)}"
    return "build complete"


@register_layout("build-output")
class BuildOutputLayout(Layout[BuildOutput]):
    @classmethod
    def to_simple(cls, data: BuildOutput) -> str:
        return f"[BUILD] {_build_summary(data)}"

    @classmethod
    def to_ansi(cls, data: BuildOutput) -> str:
        if data.install_error is not None or (
            data.executable_output is not None
            and data.executable_output.return_code != 0
        ):
            badge = f"{S.BRIGHT}{F.RED}[BUILD]{F.RESET}{S.RESET_ALL}"
        else:
            badge = f"{S.BRIGHT}{F.GREEN}[BUILD]{F.RESET}{S.RESET_ALL}"
        return f"{badge} {_build_summary(data)}"
