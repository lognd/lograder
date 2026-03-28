# type: ignore

from __future__ import annotations

import pytest

from lograder.common import Result
from lograder.pipeline.check.project.manifest import (
    ManifestCheck,
    ManifestCheckData,
    ManifestCheckError,
)
from lograder.pipeline.types.parcels import Manifest


def unwrap_result_payload(result: Result):
    if hasattr(result, "ok") and result.ok:
        return result.danger_ok
    elif hasattr(result, "err") and result.err:
        return result.danger_err
    return result


def test_manifest_check_data_default_name():
    data = ManifestCheckData(
        manifest_expected=Manifest.from_flat(["a"]),
        manifest_received=Manifest.from_flat(["a"]),
    )
    assert data.check_name == "Manifest Check"


def test_manifest_check_error_default_name():
    err = ManifestCheckError(
        manifest_expected=Manifest.from_flat(["a"]),
        manifest_received=Manifest.from_flat(["b"]),
    )
    assert err.check_name == "Manifest Check"


def test_manifest_check_is_concrete_step():
    assert ManifestCheck.is_abstract() is False


def test_manifest_check_valid_inputs_and_output():
    assert Manifest in ManifestCheck.get_valid_inputs()
    assert ManifestCheck.get_valid_output() is Manifest


def test_manifest_check_success_on_exact_match():
    expected = Manifest.from_flat(["a", "b"])
    received = Manifest.from_flat(["a", "b"])
    check = ManifestCheck(expected_manifest=expected, strict=False)

    gen = check(received)
    yielded = next(gen)
    payload = unwrap_result_payload(yielded)

    assert isinstance(payload, ManifestCheckData)
    assert payload.manifest_expected == expected
    assert payload.manifest_received == received

    with pytest.raises(StopIteration) as final:
        gen.send(None)
    final_payload = unwrap_result_payload(final.value.value)
    assert final_payload == received


def test_manifest_check_success_on_superset_when_non_strict():
    expected = Manifest.from_flat(["a"])
    received = Manifest.from_flat(["a", "b"])
    check = ManifestCheck(expected_manifest=expected, strict=False)

    gen = check(received)
    yielded = next(gen)
    payload = unwrap_result_payload(yielded)

    assert isinstance(payload, ManifestCheckData)
    assert payload.manifest_expected == expected
    assert payload.manifest_received == received

    with pytest.raises(StopIteration) as final:
        gen.send(None)
    final_payload = unwrap_result_payload(final.value.value)
    assert final_payload == received


def test_manifest_check_failure_on_superset_when_strict():
    expected = Manifest.from_flat(["a"])
    received = Manifest.from_flat(["a", "b"])
    check = ManifestCheck(expected_manifest=expected, strict=True)

    gen = check(received)

    final = None
    with pytest.raises(StopIteration) as exc:
        next(gen)

    final = exc.value.value
    final_payload = unwrap_result_payload(final)

    assert isinstance(final_payload, ManifestCheckError)
    assert final_payload.manifest_expected == expected
    assert final_payload.manifest_received == received


def test_manifest_check_failure_on_missing_file():
    expected = Manifest.from_flat(["a", "b"])
    received = Manifest.from_flat(["a"])
    check = ManifestCheck(expected_manifest=expected, strict=False)

    gen = check(received)

    with pytest.raises(StopIteration) as exc:
        next(gen)

    final_payload = unwrap_result_payload(exc.value.value)
    assert isinstance(final_payload, ManifestCheckError)
    assert final_payload.manifest_expected == expected
    assert final_payload.manifest_received == received
