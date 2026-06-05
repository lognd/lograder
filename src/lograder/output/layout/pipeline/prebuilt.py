from __future__ import annotations

from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.build.prebuilt import (
    PrebuiltArtifactsData,
    PrebuiltArtifactsError,
)


@register_layout("prebuilt-artifacts-data")
class PrebuiltArtifactsDataLayout(Layout[PrebuiltArtifactsData]):
    @classmethod
    def to_ansi(cls, data: PrebuiltArtifactsData) -> str:
        names = ", ".join(f"{F.CYAN}{n}{F.RESET}" for n in data.artifact_names)
        return (
            f"{S.BRIGHT}< {F.CYAN}PREBUILT ARTIFACTS{F.RESET} >{S.RESET_ALL}\n"
            f"{F.GREEN}Loaded {len(data.artifact_names)} artifact(s):{F.RESET} {names}"
        )

    @classmethod
    def to_simple(cls, data: PrebuiltArtifactsData) -> str:
        return f"Loaded artifacts: {', '.join(data.artifact_names)}"


@register_layout("prebuilt-artifacts-error")
class PrebuiltArtifactsErrorLayout(Layout[PrebuiltArtifactsError]):
    @classmethod
    def to_ansi(cls, data: PrebuiltArtifactsError) -> str:
        return (
            f"{S.BRIGHT}< {F.RED}PREBUILT ARTIFACTS ERROR{F.RESET} >{S.RESET_ALL}\n"
            f"  {F.CYAN}{data.file}{F.RESET}: {data.message}"
        )

    @classmethod
    def to_simple(cls, data: PrebuiltArtifactsError) -> str:
        return f"[ERROR] Prebuilt artifact '{data.file}': {data.message}"
