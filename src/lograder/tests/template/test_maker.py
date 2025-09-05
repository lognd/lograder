from pathlib import Path
from typing import List, Optional, Sequence

from ..common import FilePath
from ..common.exceptions import ArgumentSpecifiedError
from ..common.validation import validate_unique_argument
from ..simple.test_maker import make_tests_from_strs
from ..test.comparison_test import ExecutableOutputComparisonTest
from .types import TemplateSubstitution


class TestCaseTemplate:
    __test__: bool = False

    def __init__(
        self,
        *,
        input_strs: Optional[Sequence[str]] = None,
        input_template_file: Optional[FilePath] = None,
        input_template_str: Optional[str] = None,
        input_substitutions: Optional[Sequence[TemplateSubstitution]] = None,
        expected_output_strs: Optional[Sequence[str]] = None,
        expected_output_template_file: Optional[FilePath] = None,
        expected_output_template_str: Optional[str] = None,
        expected_output_substitutions: Optional[Sequence[TemplateSubstitution]] = None,
        flag_sets: Optional[Sequence[List[str]]] = None,
    ):

        if input_strs is not None:
            if (
                input_template_file is not None
                or input_template_str is not None
                or input_substitutions is not None
            ):
                raise ArgumentSpecifiedError(
                    "input_strs",
                    input_template_file=input_template_file,
                    input_template_str=input_template_str,
                    input_substitutions=input_substitutions,
                )
        else:
            validate_unique_argument(
                input_template_file=input_template_file,
                input_template_str=input_template_str,
            )
            if input_template_str is None:
                assert input_template_file is not None
                with open(Path(input_template_file), "r") as f:
                    input_template_str = f.read()

            assert input_substitutions is not None
            input_strs = [
                input_template_str.format(*temp.args, **temp.kwargs)
                for temp in input_substitutions
            ]

        if expected_output_strs is not None:
            if (
                expected_output_template_file is not None
                or expected_output_template_str is not None
                or expected_output_substitutions is not None
            ):
                raise ArgumentSpecifiedError(
                    "expected_output_strs",
                    expected_output_template_file=expected_output_template_file,
                    expected_output_template_str=expected_output_template_str,
                    expected_output_substitutions=expected_output_substitutions,
                )
        else:
            validate_unique_argument(
                expected_output_template_file=expected_output_template_file,
                expected_output_template_str=expected_output_template_str,
            )
            if expected_output_template_str is None:
                assert expected_output_template_file is not None
                with open(Path(expected_output_template_file), "r") as f:
                    expected_output_template_str = f.read()

            assert expected_output_substitutions is not None
            expected_output_strs = [
                expected_output_template_str.format(*temp.args, **temp.kwargs)
                for temp in expected_output_substitutions
            ]

        self._inputs = input_strs
        self._expected_outputs = expected_output_strs
        self._flag_sets = flag_sets

    def get_flag_sets(self):
        return self._flag_sets

    def get_inputs(self):
        return self._inputs

    def get_outputs(self):
        return self._expected_outputs


def make_tests_from_template(
    names: Sequence[str],
    template: TestCaseTemplate,
    weights: Optional[Sequence[float]] = None,
) -> List[ExecutableOutputComparisonTest]:
    return make_tests_from_strs(
        names=names,
        inputs=template.get_inputs(),
        expected_outputs=template.get_outputs(),
        weights=weights,
        flag_sets=template.get_flag_sets(),
    )
