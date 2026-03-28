# type: ignore

from __future__ import annotations

import pytest

from lograder.common import Result
from lograder.pipeline.check.project.simple_project import (
    REGISTERED_TYPES,
    REQUIRED_FILES,
    get_check_cls,
    get_data_cls,
    get_error_cls,
    get_manifest_cls,
    make_simple_manifest_checker,
)
from lograder.pipeline.types.parcels import Manifest


def unwrap_result_payload(result: Result):
    if hasattr(result, "ok") and result.ok:
        return result.danger_ok
    elif hasattr(result, "err") and result.err:
        return result.danger_err
    return result


@pytest.mark.parametrize(
    ("project_name", "required_file", "display_name"),
    [
        ("CMake", "CMakeLists.txt", "CMake Manifest Check"),
        ("Makefile", "Makefile", "Makefile Manifest Check"),
        ("PyProject", "pyproject.toml", "PyProject Manifest Check"),
    ],
)
def test_make_simple_manifest_checker_names(project_name, required_file, display_name):
    manifest_cls, data_cls, error_cls, check_cls = make_simple_manifest_checker(
        project_name, [required_file]
    )

    assert manifest_cls.__name__ == f"{project_name}Manifest"
    assert data_cls.__name__ == f"{project_name}ManifestCheckData"
    assert error_cls.__name__ == f"{project_name}ManifestCheckError"
    assert check_cls.__name__ == f"{project_name}ManifestCheck"

    data = data_cls(
        manifest_expected=Manifest.from_flat([required_file]),
        manifest_received=Manifest.from_flat([required_file]),
    )
    err = error_cls(
        manifest_expected=Manifest.from_flat([required_file]),
        manifest_received=Manifest.from_flat([]),
    )

    assert data.check_name == display_name
    assert err.check_name == display_name


@pytest.mark.parametrize("project_name", ["CMake", "Makefile", "PyProject"])
def test_registered_types_populated(project_name):
    assert project_name in REGISTERED_TYPES
    manifest_cls, data_cls, error_cls, check_cls = REGISTERED_TYPES[project_name]

    assert get_manifest_cls(project_name) is manifest_cls
    assert get_data_cls(project_name) is data_cls
    assert get_error_cls(project_name) is error_cls
    assert get_check_cls(project_name) is check_cls


@pytest.mark.parametrize("project_name", ["CMake", "Makefile", "PyProject"])
def test_generated_check_is_concrete_step(project_name):
    check_cls = get_check_cls(project_name)
    assert check_cls.is_abstract() is False


@pytest.mark.parametrize("project_name", ["CMake", "Makefile", "PyProject"])
def test_generated_check_valid_inputs_and_output(project_name):
    check_cls = get_check_cls(project_name)
    manifest_cls = get_manifest_cls(project_name)

    assert Manifest in check_cls.get_valid_inputs()
    assert check_cls.get_valid_output() is manifest_cls


@pytest.mark.parametrize(
    ("project_name", "required_file"),
    [
        ("CMake", "CMakeLists.txt"),
        ("Makefile", "Makefile"),
        ("PyProject", "pyproject.toml"),
    ],
)
def test_generated_check_success(project_name, required_file):
    check_cls = get_check_cls(project_name)
    data_cls = get_data_cls(project_name)
    manifest_cls = get_manifest_cls(project_name)

    check = check_cls()
    received = Manifest.from_flat([required_file])

    gen = check(received)
    yielded = next(gen)
    payload = unwrap_result_payload(yielded)

    assert isinstance(payload, data_cls)
    assert payload.manifest_received == received
    assert payload.manifest_expected == Manifest.from_flat([required_file])

    with pytest.raises(StopIteration) as final:
        gen.send(None)
    final_payload = unwrap_result_payload(final.value.value)
    assert isinstance(final_payload, manifest_cls)
    assert final_payload == manifest_cls(received)


@pytest.mark.parametrize(
    ("project_name", "required_file"),
    [
        ("CMake", "CMakeLists.txt"),
        ("Makefile", "Makefile"),
        ("PyProject", "pyproject.toml"),
    ],
)
def test_generated_check_failure_when_required_file_missing(
    project_name, required_file
):
    check_cls = get_check_cls(project_name)
    error_cls = get_error_cls(project_name)

    check = check_cls()
    received = Manifest.from_flat([])

    gen = check(received)

    with pytest.raises(StopIteration) as exc:
        next(gen)

    final_payload = unwrap_result_payload(exc.value.value)
    assert isinstance(final_payload, error_cls)
    assert final_payload.manifest_received == received
    assert final_payload.manifest_expected == Manifest.from_flat([required_file])


@pytest.mark.parametrize("project_name", ["CMake", "Makefile", "PyProject"])
def test_generated_check_accepts_superset_manifest(project_name):
    required_files = REQUIRED_FILES[project_name]
    extra = ["extra.txt"]
    received = Manifest.from_flat([*required_files, *extra])

    check_cls = get_check_cls(project_name)
    check = check_cls()

    gen = check(received)
    yielded = next(gen)
    payload = unwrap_result_payload(yielded)

    assert payload.manifest_received == received

    with pytest.raises(StopIteration) as final:
        gen.send(None)
    final_payload = unwrap_result_payload(final.value.value)
    assert isinstance(final_payload, get_manifest_cls(project_name))
