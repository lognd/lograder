import pytest

from lograder.exception import StaffException
from lograder.pipeline.config import config
from lograder.pipeline.input.local_directory import LocalDirectory
from lograder.pipeline.mixin.mixin import (
    InjectStaffIntoStudent,
    InjectStudentIntoStaff,
    MixinData,
)
from lograder.pipeline.pipeline import Pipeline
from lograder.pipeline.types.parcels import Manifest


@pytest.mark.slow
def test_inject_student_into_staff_copies_all_files(tmp_path):
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
        gen = step(manifest)
        packets = []
        try:
            while True:
                packets.append(next(gen))
        except StopIteration as e:
            result = e.value

    assert result.is_ok
    assert (staff / "main.c").exists()
    assert (staff / "helper.c").exists()


@pytest.mark.slow
def test_inject_student_into_staff_with_filter(tmp_path):
    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("", encoding="utf-8")
    (student / "other.c").write_text("", encoding="utf-8")

    staff = tmp_path / "staff"
    staff.mkdir()

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStudentIntoStaff(staff, student_files=["main.c"])
        gen = step(manifest)
        try:
            while True:
                next(gen)
        except StopIteration:
            pass

    assert (staff / "main.c").exists()
    assert not (staff / "other.c").exists()


@pytest.mark.slow
def test_inject_student_into_staff_overwrite_false(tmp_path):
    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("NEW", encoding="utf-8")

    staff = tmp_path / "staff"
    staff.mkdir()
    (staff / "main.c").write_text("OLD", encoding="utf-8")

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStudentIntoStaff(staff, overwrite=False)
        gen = step(manifest)
        try:
            while True:
                next(gen)
        except StopIteration:
            pass

    assert (staff / "main.c").read_text(encoding="utf-8") == "OLD"


@pytest.mark.slow
def test_inject_student_into_staff_overwrite_true(tmp_path):
    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("NEW", encoding="utf-8")

    staff = tmp_path / "staff"
    staff.mkdir()
    (staff / "main.c").write_text("OLD", encoding="utf-8")

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStudentIntoStaff(staff, overwrite=True)
        gen = step(manifest)
        try:
            while True:
                next(gen)
        except StopIteration:
            pass

    assert (staff / "main.c").read_text(encoding="utf-8") == "NEW"


@pytest.mark.slow
def test_inject_student_into_staff_returns_staff_manifest(tmp_path):
    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("", encoding="utf-8")

    staff = tmp_path / "staff"
    staff.mkdir()

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStudentIntoStaff(staff)
        gen = step(manifest)
        try:
            while True:
                next(gen)
        except StopIteration as e:
            result = e.value

    assert result.danger_ok.root == staff


@pytest.mark.slow
def test_inject_staff_into_student_copies_all_files(tmp_path):
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
        gen = step(manifest)
        try:
            while True:
                next(gen)
        except StopIteration as e:
            result = e.value

    assert result.is_ok
    assert (student / "grader.h").exists()
    assert (student / "harness.c").exists()


@pytest.mark.slow
def test_inject_staff_into_student_with_filter(tmp_path):
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
        gen = step(manifest)
        try:
            while True:
                next(gen)
        except StopIteration:
            pass

    assert (student / "grader.h").exists()
    assert not (student / "extra.h").exists()


@pytest.mark.slow
def test_inject_staff_into_student_overwrite_false(tmp_path):
    staff_src = tmp_path / "staff_src"
    staff_src.mkdir()
    (staff_src / "grader.h").write_text("NEW", encoding="utf-8")

    student = tmp_path / "student"
    student.mkdir()
    (student / "grader.h").write_text("OLD", encoding="utf-8")

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStaffIntoStudent(staff_src, overwrite=False)
        gen = step(manifest)
        try:
            while True:
                next(gen)
        except StopIteration:
            pass

    assert (student / "grader.h").read_text(encoding="utf-8") == "OLD"


@pytest.mark.slow
def test_inject_staff_into_student_returns_student_manifest(tmp_path):
    staff_src = tmp_path / "staff_src"
    staff_src.mkdir()
    (staff_src / "grader.h").write_text("", encoding="utf-8")

    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("", encoding="utf-8")

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStaffIntoStudent(staff_src)
        gen = step(manifest)
        try:
            while True:
                next(gen)
        except StopIteration as e:
            result = e.value

    assert result.danger_ok.root == student


@pytest.mark.slow
def test_inject_student_into_staff_in_pipeline(tmp_path):
    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("int main(){}", encoding="utf-8")

    staff = tmp_path / "staff"
    staff.mkdir()
    (staff / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.10)", encoding="utf-8"
    )

    pipeline = Pipeline()
    pipeline.steps = [
        LocalDirectory(student),
        InjectStudentIntoStaff(staff),
    ]

    with config(root_directory=tmp_path):
        score = pipeline()

    assert pipeline.datum.root == staff


@pytest.mark.slow
def test_inject_staff_into_student_in_pipeline(tmp_path):
    staff_src = tmp_path / "staff_src"
    staff_src.mkdir()
    (staff_src / "grader.h").write_text("#define GRADE 1", encoding="utf-8")

    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("int main(){}", encoding="utf-8")

    pipeline = Pipeline()
    pipeline.steps = [
        LocalDirectory(student),
        InjectStaffIntoStudent(staff_src),
    ]

    with config(root_directory=tmp_path):
        score = pipeline()

    assert "grader.h" in pipeline.datum


@pytest.mark.slow
def test_inject_student_into_staff_init_nonexistent_raises(tmp_path):
    with pytest.raises(StaffException):
        InjectStudentIntoStaff(tmp_path / "nonexistent")


@pytest.mark.slow
def test_inject_staff_into_student_init_nonexistent_raises(tmp_path):
    with pytest.raises(StaffException):
        InjectStaffIntoStudent(tmp_path / "nonexistent")


@pytest.mark.slow
def test_mixin_yields_mixin_data_packet(tmp_path):
    student = tmp_path / "student"
    student.mkdir()
    (student / "main.c").write_text("", encoding="utf-8")

    staff = tmp_path / "staff"
    staff.mkdir()

    with config(root_directory=tmp_path):
        manifest = Manifest.from_directory(student)
        step = InjectStudentIntoStaff(staff)
        packets = []
        gen = step(manifest)
        try:
            while True:
                packets.append(next(gen))
        except StopIteration:
            pass

    assert len(packets) == 1
    assert packets[0].is_ok
    data = packets[0].danger_ok
    assert isinstance(data, MixinData)
    assert data.source_directory == student
    assert data.destination_directory == staff
    assert "main.c" in data.files_copied
