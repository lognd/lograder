# noinspection PyPep8Naming
from colorama import Fore as F
from colorama import Style as S

from ...pipeline.check import ManifestCheckData, ManifestCheckError
from ...pipeline.config import get_config
from .format_helpers.manifest import render_manifest_diff, render_manifest_tree
from .layout import Layout, register_layout


# noinspection DuplicatedCode
@register_layout("manifest-check-data")
class ManifestCheckDataLayout(Layout[ManifestCheckData]):
    @classmethod
    def to_ansi(cls, data: ManifestCheckData) -> str:
        root_directory = get_config().root_directory
        tree = render_manifest_tree(
            data.manifest_expected.directory_mapping,
            data.manifest_received.directory_mapping,
        )
        tree_ansi = "\n".join("".join(line) for line in tree)
        return (
            f"{S.BRIGHT}< {F.CYAN}MANIFEST CHECK{F.RESET} >{S.RESET_ALL}\n"
            f"{F.GREEN}The received manifest is compliant with the expected manifest.{F.RESET}\n\n"
            f"{str(root_directory)}/\n"
            f"{tree_ansi}"
        )

    @classmethod
    def to_simple(cls, data: ManifestCheckData) -> str:
        diff = render_manifest_diff(
            data.manifest_expected.directory_mapping,
            data.manifest_received.directory_mapping,
        )
        return f"The received manifest is compliant with the expected manifest; {diff}"


# Somewhat duplicated, but this code is very unlikely to reappear, so no use in collecting it.
# noinspection DuplicatedCode
@register_layout("manifest-check-error")
class ManifestCheckErrorLayout(Layout[ManifestCheckError]):
    @classmethod
    def to_ansi(cls, data: ManifestCheckError) -> str:
        root_directory = get_config().root_directory
        tree = render_manifest_tree(
            data.manifest_expected.directory_mapping,
            data.manifest_received.directory_mapping,
        )
        tree_ansi = "\n".join("".join(line) for line in tree)
        return (
            f"{S.BRIGHT}< {F.CYAN}MANIFEST CHECK{F.RESET} >{S.RESET_ALL}\n"
            f"{F.RED}The received manifest does not fit the expected manifest.{F.RESET}\n\n"
            f"{str(root_directory)}/\n"
            f"{tree_ansi}"
        )

    @classmethod
    def to_simple(cls, data: ManifestCheckError) -> str:
        diff = render_manifest_diff(
            data.manifest_expected.directory_mapping,
            data.manifest_received.directory_mapping,
        )
        return f"The received manifest does not fit the expected manifest; {diff}"
