"""Regression guard for design/lograder.strata: the architecture model
must keep proving clean under `frob sys audit` (T-0005)."""

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
STRATA_MODEL = REPO_ROOT / "design" / "lograder.strata"


def test_strata_model_exists() -> None:
    """The self-model landed with T-0005 and must not silently disappear."""
    assert STRATA_MODEL.is_file()


@pytest.mark.skipif(shutil.which("frob") is None, reason="frob not on PATH")
def test_frob_sys_audit_proves_clean() -> None:
    """`frob sys audit` must exit 0 (PROVED) -- a refuted claim or an
    undischarged capability obligation in the model is a regression."""
    result = subprocess.run(
        ["frob", "sys", "audit"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        f"frob sys audit failed:\n{result.stdout}\n{result.stderr}"
    )
