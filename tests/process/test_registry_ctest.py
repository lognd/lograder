from __future__ import annotations

import pytest

from lograder.process.registry.ctest import CTestArgs, CTestExecutable

# ---------------------------------------------------------------------------
# CTestArgs emit
# ---------------------------------------------------------------------------


def test_default_args_emit_empty():
    args = CTestArgs()
    assert args.emit() == []


def test_test_regex():
    args = CTestArgs(test_regex="Math.*")
    tokens = args.emit()
    assert "-R" in tokens
    assert "Math.*" in tokens


def test_exclude_regex():
    args = CTestArgs(exclude_regex="Slow")
    tokens = args.emit()
    assert "-E" in tokens
    assert "Slow" in tokens


def test_label_regex():
    args = CTestArgs(label_regex="unit")
    tokens = args.emit()
    assert "-L" in tokens
    assert "unit" in tokens


def test_exclude_label_regex():
    args = CTestArgs(exclude_label_regex="integration")
    tokens = args.emit()
    assert "-LE" in tokens
    assert "integration" in tokens


def test_tests_index():
    args = CTestArgs(tests_index="1,3,5")
    tokens = args.emit()
    assert "-I" in tokens
    assert "1,3,5" in tokens


def test_rerun_failed():
    args = CTestArgs(rerun_failed=True)
    assert "--rerun-failed" in args.emit()


def test_run_disabled():
    args = CTestArgs(run_disabled=True)
    assert "--run-disabled" in args.emit()


def test_parallel():
    args = CTestArgs(parallel=4)
    tokens = args.emit()
    assert "-j" in tokens
    assert "4" in tokens


def test_timeout():
    args = CTestArgs(timeout=30.0)
    tokens = args.emit()
    assert "--timeout" in tokens
    assert "30.0" in tokens


def test_stop_on_failure():
    args = CTestArgs(stop_on_failure=True)
    assert "--stop-on-failure" in args.emit()


def test_schedule_random():
    args = CTestArgs(schedule_random=True)
    assert "--schedule-random" in args.emit()


def test_repeat():
    args = CTestArgs(repeat="until-fail:3")
    tokens = args.emit()
    assert "--repeat" in tokens
    assert "until-fail:3" in tokens


def test_build_config():
    args = CTestArgs(build_config="Release")
    tokens = args.emit()
    assert "-C" in tokens
    assert "Release" in tokens


def test_test_dir(tmp_path):
    args = CTestArgs(test_dir=tmp_path)
    tokens = args.emit()
    assert "--test-dir" in tokens
    assert str(tmp_path) in tokens


def test_output_junit(tmp_path):
    p = tmp_path / "results.xml"
    args = CTestArgs(output_junit=p)
    tokens = args.emit()
    assert "--output-junit" in tokens
    assert str(p) in tokens


def test_output_on_failure():
    args = CTestArgs(output_on_failure=True)
    assert "--output-on-failure" in args.emit()


def test_verbose():
    args = CTestArgs(verbose=True)
    assert "-V" in args.emit()


def test_extra_verbose():
    args = CTestArgs(extra_verbose=True)
    assert "-VV" in args.emit()


def test_quiet():
    args = CTestArgs(quiet=True)
    assert "-Q" in args.emit()


def test_show_only():
    args = CTestArgs(show_only=True)
    assert "-N" in args.emit()


def test_print_labels():
    args = CTestArgs(print_labels=True)
    assert "--print-labels" in args.emit()


def test_ctest_executable_instantiable():
    exe = CTestExecutable()
    assert exe is not None


def test_ctest_check_runnable_returns_result():
    exe = CTestExecutable()
    result = exe.check_runnable()
    assert result.is_ok or result.is_err


# --- Real executable tests ---

import shutil as _shutil  # noqa: E402
import subprocess as _subprocess  # noqa: E402

_CTEST_AVAILABLE = bool(_shutil.which("ctest"))
_CMAKE_AVAILABLE = bool(_shutil.which("cmake"))
_GCC_AVAILABLE = bool(_shutil.which("gcc"))

_BOTH_AVAILABLE = _CTEST_AVAILABLE and _CMAKE_AVAILABLE and _GCC_AVAILABLE

_CMAKELISTS = """\
cmake_minimum_required(VERSION 3.10)
project(hello C)
add_executable(hello main.c)
add_test(NAME always_passes COMMAND hello)
"""
_MAIN_C = '#include <stdio.h>\nint main(void){puts("ok");return 0;}\n'


@pytest.mark.skipif(not _BOTH_AVAILABLE, reason="ctest, cmake, and gcc all required")
@pytest.mark.slow
def test_ctest_real_runs_cmake_test(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "CMakeLists.txt").write_text(_CMAKELISTS, encoding="utf-8")
    (src_dir / "main.c").write_text(_MAIN_C, encoding="utf-8")
    build_dir = tmp_path / "build"
    build_dir.mkdir()

    _subprocess.run(
        ["cmake", str(src_dir), "-B", str(build_dir)],
        check=True,
        capture_output=True,
    )
    _subprocess.run(
        ["cmake", "--build", str(build_dir)],
        check=True,
        capture_output=True,
    )

    exe = CTestExecutable()
    args = CTestArgs(test_dir=build_dir, output_on_failure=True)
    result = exe(args, options=ExecutableOptions(cwd=build_dir))
    assert result.is_ok
    assert result.danger_ok.return_code == 0


@pytest.mark.skipif(not _BOTH_AVAILABLE, reason="ctest, cmake, and gcc all required")
@pytest.mark.slow
def test_ctest_real_junit_output(tmp_path) -> None:
    from lograder.process.executable import ExecutableOptions

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "CMakeLists.txt").write_text(_CMAKELISTS, encoding="utf-8")
    (src_dir / "main.c").write_text(_MAIN_C, encoding="utf-8")
    build_dir = tmp_path / "build"
    build_dir.mkdir()

    _subprocess.run(
        ["cmake", str(src_dir), "-B", str(build_dir)],
        check=True,
        capture_output=True,
    )
    _subprocess.run(
        ["cmake", "--build", str(build_dir)],
        check=True,
        capture_output=True,
    )
    xml_out = tmp_path / "results.xml"

    exe = CTestExecutable()
    args = CTestArgs(test_dir=build_dir, output_junit=xml_out)
    result = exe(args, options=ExecutableOptions(cwd=build_dir))
    assert result.is_ok
    assert result.danger_ok.return_code == 0
    assert xml_out.exists()
    assert b"testsuite" in xml_out.read_bytes()
