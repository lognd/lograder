# mypy: ignore-errors

import pytest

from lograder.exception import StaffException
from lograder.pipeline.config import config
from lograder.pipeline.mixin.mixin import (
    InjectStaffIntoStudent,
    InjectStudentIntoStaff,
    MixinData,
)
from lograder.pipeline.types.parcels import Manifest


def _run_step(step, manifest):
    gen = step(manifest)
    packets = []
    try:
        while True:
            packets.append(next(gen))
    except StopIteration as e:
        return packets, e.value


def test_inject_student_into_staff_nonexistent_dir_raises(tmp_path):
    with pytest.raises(StaffException):
        InjectStudentIntoStaff(tmp_path / "nonexistent")


def test_inject_student_into_staff_file_as_dir_raises(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(StaffException):
        InjectStudentIntoStaff(f)


def test_inject_staff_into_student_nonexistent_source_raises(tmp_path):
    with pytest.raises(StaffException):
        InjectStaffIntoStudent(tmp_path / "nonexistent")


def test_inject_student_copies_all_files(tmp_path):
    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("int main(){}", encoding="utf-8")
    (student / "helper.c").write_text("", encoding="utf-8")

    staff = tmp_path / "staff"
    staff.mkdir()
    (staff / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.10)", encoding="utf-8"
    )

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStudentIntoStaff(staff)
        _, result = _run_step(step, manifest)

    assert result.is_ok
    assert (staff / "main.c").exists()
    assert (staff / "helper.c").exists()


def test_inject_student_copies_nested_files(tmp_path):
    student = tmp_path / "student"
    (student / "src").mkdir(parents=True)
    (student / "src" / "deep.c").write_text("", encoding="utf-8")

    staff = tmp_path / "staff"
    staff.mkdir()

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStudentIntoStaff(staff)
        _, result = _run_step(step, manifest)

    assert (staff / "src" / "deep.c").exists()


def test_inject_student_with_filter_copies_subset(tmp_path):
    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("", encoding="utf-8")
    (student / "other.c").write_text("", encoding="utf-8")

    staff = tmp_path / "staff"
    staff.mkdir()

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStudentIntoStaff(staff, student_files=["main.c"])
        _, result = _run_step(step, manifest)

    assert (staff / "main.c").exists()
    assert not (staff / "other.c").exists()


def test_inject_student_overwrite_true_replaces_existing(tmp_path):
    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("NEW", encoding="utf-8")

    staff = tmp_path / "staff"
    staff.mkdir()
    (staff / "main.c").write_text("OLD", encoding="utf-8")

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStudentIntoStaff(staff, overwrite=True)
        _run_step(step, manifest)

    assert (staff / "main.c").read_text(encoding="utf-8") == "NEW"


def test_inject_student_overwrite_false_keeps_existing(tmp_path):
    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("NEW", encoding="utf-8")

    staff = tmp_path / "staff"
    staff.mkdir()
    (staff / "main.c").write_text("OLD", encoding="utf-8")

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStudentIntoStaff(staff, overwrite=False)
        _run_step(step, manifest)

    assert (staff / "main.c").read_text(encoding="utf-8") == "OLD"


def test_inject_student_yields_mixin_data_with_correct_fields(tmp_path):
    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("", encoding="utf-8")

    staff = tmp_path / "staff"
    staff.mkdir()

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStudentIntoStaff(staff)
        packets, _ = _run_step(step, manifest)

    assert len(packets) == 1
    assert packets[0].is_ok
    data = packets[0].danger_ok
    assert isinstance(data, MixinData)
    assert data.source_directory == student
    assert data.destination_directory == staff
    assert "main.c" in data.files_copied


def test_inject_student_returns_staff_manifest(tmp_path):
    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("", encoding="utf-8")

    staff = tmp_path / "staff"
    staff.mkdir()
    (staff / "CMakeLists.txt").write_text("", encoding="utf-8")

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStudentIntoStaff(staff)
        _, result = _run_step(step, manifest)

    assert result.is_ok
    assert result.danger_ok.root == staff


def test_inject_staff_copies_all_files(tmp_path):
    staff_src = tmp_path / "staff_src"
    staff_src.mkdir()
    (staff_src / "grader.h").write_text("#define GRADE 1", encoding="utf-8")
    (staff_src / "harness.c").write_text("", encoding="utf-8")

    student = tmp_path / "student"
    student.mkdir()
    (student / "CMakeLists.txt").write_text("", encoding="utf-8")

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStaffIntoStudent(staff_src)
        _, result = _run_step(step, manifest)

    assert (student / "grader.h").exists()
    assert (student / "harness.c").exists()


def test_inject_staff_with_filter_copies_subset(tmp_path):
    staff_src = tmp_path / "staff_src"
    staff_src.mkdir()
    (staff_src / "grader.h").write_text("", encoding="utf-8")
    (staff_src / "extra.h").write_text("", encoding="utf-8")

    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("", encoding="utf-8")

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStaffIntoStudent(staff_src, staff_files=["grader.h"])
        _run_step(step, manifest)

    assert (student / "grader.h").exists()
    assert not (student / "extra.h").exists()


def test_inject_staff_overwrite_true_replaces_existing(tmp_path):
    staff_src = tmp_path / "staff_src"
    staff_src.mkdir()
    (staff_src / "grader.h").write_text("NEW", encoding="utf-8")

    student = tmp_path / "student"
    student.mkdir()
    (student / "grader.h").write_text("OLD", encoding="utf-8")

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStaffIntoStudent(staff_src, overwrite=True)
        _run_step(step, manifest)

    assert (student / "grader.h").read_text(encoding="utf-8") == "NEW"


def test_inject_staff_overwrite_false_keeps_existing(tmp_path):
    staff_src = tmp_path / "staff_src"
    staff_src.mkdir()
    (staff_src / "grader.h").write_text("NEW", encoding="utf-8")

    student = tmp_path / "student"
    student.mkdir()
    (student / "grader.h").write_text("OLD", encoding="utf-8")

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStaffIntoStudent(staff_src, overwrite=False)
        _run_step(step, manifest)

    assert (student / "grader.h").read_text(encoding="utf-8") == "OLD"


def test_inject_staff_yields_mixin_data(tmp_path):
    staff_src = tmp_path / "staff_src"
    staff_src.mkdir()
    (staff_src / "grader.h").write_text("", encoding="utf-8")

    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("", encoding="utf-8")

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStaffIntoStudent(staff_src)
        packets, _ = _run_step(step, manifest)

    assert len(packets) == 1
    assert packets[0].is_ok
    data = packets[0].danger_ok
    assert isinstance(data, MixinData)
    assert data.source_directory == staff_src
    assert data.destination_directory == student


def test_inject_staff_returns_updated_student_manifest(tmp_path):
    staff_src = tmp_path / "staff_src"
    staff_src.mkdir()
    (staff_src / "grader.h").write_text("", encoding="utf-8")

    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("", encoding="utf-8")

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStaffIntoStudent(staff_src)
        _, result = _run_step(step, manifest)

    assert result.is_ok
    returned = result.danger_ok
    assert returned.root == student
    assert "grader.h" in returned
