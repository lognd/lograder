# mypy: ignore-errors
from abc import abstractmethod
from typing import Generator, TypeVar

import pytest
from pydantic import BaseModel

from lograder.common import Err, Ok, Result
from lograder.exception import DeveloperException, StaffException
from lograder.pipeline.step import Step
from lograder.pipeline.types.sentinel import PIPELINE_START

_IT = TypeVar("_IT")
_OT = TypeVar("_OT")
_ET = TypeVar("_ET")
_DT = TypeVar("_DT")


class _D(BaseModel):
    pass


class _E(BaseModel):
    pass


def test_concrete_step_without_params_raises():
    with pytest.raises(DeveloperException):

        class BadStep(Step):
            def __call__(self, input):
                if False:
                    yield
                return Ok(1)


def test_concrete_step_with_wrong_count_raises():
    with pytest.raises((DeveloperException, TypeError)):

        class BadStep(Step[PIPELINE_START, int, _E]):
            def __call__(self, input):
                if False:
                    yield
                return Ok(1)


def test_concrete_step_with_5_params_succeeds():
    class GoodStep(Step[PIPELINE_START, int, _E, _D, _E]):
        def __call__(
            self, input: PIPELINE_START
        ) -> Generator[Result[_D, _E], None, Result[int, _E]]:
            if False:
                yield Ok(_D())
            return Ok(42)

    assert not GoodStep.is_abstract()


def test_step_valid_input_types_set_on_concrete():
    class MyStep(Step[PIPELINE_START, int, _E, _D, _E]):
        def __call__(self, input):
            if False:
                yield Ok(_D())
            return Ok(1)

    assert PIPELINE_START in MyStep.get_valid_inputs()


def test_step_valid_output_type_set_on_concrete():
    class MyStep(Step[PIPELINE_START, int, _E, _D, _E]):
        def __call__(self, input):
            if False:
                yield Ok(_D())
            return Ok(1)

    assert MyStep.get_valid_output() is int


def test_step_union_input_accepted():
    class MyStep(Step[PIPELINE_START | int, str, _E, _D, _E]):
        def __call__(self, input):
            if False:
                yield Ok(_D())
            return Ok("hello")

    inputs = MyStep.get_valid_inputs()
    assert PIPELINE_START in inputs
    assert int in inputs


def test_is_follow_matching_types():
    class StepA(Step[PIPELINE_START, int, _E, _D, _E]):
        def __call__(self, input):
            if False:
                yield Ok(_D())
            return Ok(1)

    class StepB(Step[int, str, _E, _D, _E]):
        def __call__(self, input):
            if False:
                yield Ok(_D())
            return Ok("hi")

    assert StepB.is_follow(StepA)


def test_is_follow_non_matching_types():
    class StepA(Step[PIPELINE_START, int, _E, _D, _E]):
        def __call__(self, input):
            if False:
                yield Ok(_D())
            return Ok(1)

    class StepB(Step[str, float, _E, _D, _E]):
        def __call__(self, input):
            if False:
                yield Ok(_D())
            return Ok(1.0)

    assert not StepB.is_follow(StepA)


def test_assert_follow_raises_developer_exception_by_default():
    class StepA(Step[PIPELINE_START, int, _E, _D, _E]):
        def __call__(self, input):
            if False:
                yield Ok(_D())
            return Ok(1)

    class StepB(Step[str, float, _E, _D, _E]):
        def __call__(self, input):
            if False:
                yield Ok(_D())
            return Ok(1.0)

    with pytest.raises(DeveloperException):
        StepB.assert_follow(StepA)


def test_assert_follow_can_raise_staff_exception():
    class StepA(Step[PIPELINE_START, int, _E, _D, _E]):
        def __call__(self, input):
            if False:
                yield Ok(_D())
            return Ok(1)

    class StepB(Step[str, float, _E, _D, _E]):
        def __call__(self, input):
            if False:
                yield Ok(_D())
            return Ok(1.0)

    with pytest.raises(StaffException):
        StepB.assert_follow(StepA, origin_exception_type=StaffException)


def test_is_abstract_on_abstract_step():
    class AbstractStep(Step[_IT, _OT, _ET, _DT, _ET]):
        @abstractmethod
        def __call__(self, input):
            pass

    assert AbstractStep.is_abstract()


def test_is_abstract_on_concrete_step():
    class ConcreteStep(Step[PIPELINE_START, int, _E, _D, _E]):
        def __call__(self, input):
            if False:
                yield Ok(_D())
            return Ok(1)

    assert not ConcreteStep.is_abstract()


def test_get_valid_inputs_on_abstract_raises():
    class AbstractStep(Step[_IT, _OT, _ET, _DT, _ET]):
        @abstractmethod
        def __call__(self, input):
            pass

    with pytest.raises(DeveloperException):
        AbstractStep.get_valid_inputs()
