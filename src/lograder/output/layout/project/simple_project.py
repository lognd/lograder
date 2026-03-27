# noinspection PyPep8Naming
from colorama import Fore as F
from colorama import Style as S

from lograder.output.layout.dynamic import make_dynamic_layout
from lograder.output.layout.format_helpers.manifest import (
    render_manifest_diff,
    render_manifest_tree,
)
from lograder.output.layout.layout import Layout, LayoutLike
from lograder.pipeline.check.project.manifest import (
    ManifestCheckData,
    ManifestCheckError,
)
from lograder.pipeline.check.project.simple_project import (
    REQUIRED_FILES,
    ProjectType,
    get_data_cls,
    get_error_cls,
)


def make_simple_layout_checker(
    project_name: ProjectType,
) -> tuple[type[Layout], type[Layout]]:
    # noinspection DuplicatedCode
    def to_ansi_data(_: type[Layout], data: ManifestCheckData) -> str:
        tree = render_manifest_tree(
            data.manifest_expected.directory_mapping,
            data.manifest_received.directory_mapping,
        )
        tree_ansi = "\n".join("".join(line) for line in tree)
        return (
            f"{S.BRIGHT}< {F.CYAN}{project_name.upper()} MANIFEST CHECK{F.RESET} >{S.RESET_ALL}\n"
            f"{F.GREEN}The received manifest is compliant with what is expected for a {project_name} project.{F.RESET}\n\n"
            f"<project-root>/\n"
            f"{tree_ansi}"
        )

    # noinspection DuplicatedCode
    def to_simple_data(_: type[Layout], data: ManifestCheckData) -> str:
        diff = render_manifest_diff(
            data.manifest_expected.directory_mapping,
            data.manifest_received.directory_mapping,
        )
        return f"The received manifest is compliant with what is expected for a {project_name} project; {diff}"

    layout_data = make_dynamic_layout(
        layout_id=f"{project_name.lower()}-check-data",
        layout_type=get_data_cls(project_name),
        layout_cls_name=f"{project_name}ProjectManifestCheckDataLayout",
        layout_like=LayoutLike(to_ansi=to_ansi_data, to_simple=to_simple_data),
    )

    # noinspection DuplicatedCode
    def to_ansi_error(_: type[Layout], data: ManifestCheckError) -> str:
        tree = render_manifest_tree(
            data.manifest_expected.directory_mapping,
            data.manifest_received.directory_mapping,
        )
        tree_ansi = "\n".join("".join(line) for line in tree)
        return (
            f"{S.BRIGHT}< {F.CYAN}{project_name.upper()} MANIFEST CHECK{F.RESET} >{S.RESET_ALL}\n"
            f"{F.RED}The received manifest does not fit the expected manifest for a {project_name} project.{F.RESET}\n\n"
            f"<project-root>/\n"
            f"{tree_ansi}"
        )

    # noinspection DuplicatedCode
    def to_simple_error(_: type[Layout], data: ManifestCheckError) -> str:
        diff = render_manifest_diff(
            data.manifest_expected.directory_mapping,
            data.manifest_received.directory_mapping,
        )
        return f"The received manifest does not fit the expected manifest for a {project_name} project; {diff}"

    layout_error = make_dynamic_layout(
        layout_id=f"{project_name.lower()}-check-error",
        layout_type=get_error_cls(project_name),
        layout_cls_name=f"{project_name}ProjectManifestCheckErrorLayout",
        layout_like=LayoutLike(to_ansi=to_ansi_error, to_simple=to_simple_error),
    )

    return layout_data, layout_error


for project_name in REQUIRED_FILES:
    layout_data, layout_error = make_simple_layout_checker(project_name)
    globals()[layout_data.__name__] = layout_data
    globals()[layout_error.__name__] = layout_error
