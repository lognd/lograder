from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.layout import Layout, register_layout
from lograder.pipeline.mixin.mixin import MixinData


@register_layout("mixin-data")
class MixinDataLayout(Layout[MixinData]):
    @classmethod
    def to_simple(cls, data: MixinData) -> str:
        n = len(data.files_copied)
        lines = [
            f"[MIXIN] Copied {n} file(s):",
            f"  from: {data.source_directory}",
            f"  to:   {data.destination_directory}",
        ]
        for f_name in data.files_copied:
            lines.append(f"    {f_name}")
        return "\n".join(lines)

    @classmethod
    def to_ansi(cls, data: MixinData) -> str:
        n = len(data.files_copied)
        lines = [
            f"{S.BRIGHT}{F.BLUE}[MIXIN]{F.RESET}{S.RESET_ALL} Copied {n} file(s):",
            f"  from: {F.CYAN}{data.source_directory}{F.RESET}",
            f"  to:   {F.CYAN}{data.destination_directory}{F.RESET}",
        ]
        for f_name in data.files_copied:
            lines.append(f"    {F.WHITE}{f_name}{F.RESET}")
        return "\n".join(lines)
