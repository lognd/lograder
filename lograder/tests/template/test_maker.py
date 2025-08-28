from typing import Optional, Sequence

from ..common import FilePath
from .types import TemplateSubstitution

class TestCaseTemplate:
    def __init__(self, *,
                 inputs: Optional[Sequence[str]] = None,
                 input_template_file: Optional[FilePath] = None,
                 input_template_str: Optional[str] = None,
                 input_substitutions: Optional[Sequence[TemplateSubstitution]] = None,
                 expected_outputs: Optional[Sequence[str]] = None,
                 expected_output_template_file: Optional[FilePath] = None,
                 expected_output_template_str: Optional[str] = None,
                 expected_output_substitutions: Optional[Sequence[TemplateSubstitution]] = None,
                 ):
        # TODO: Make implementation of the `TestCaseTemplate` class.
        ...

def make_tests_from_template(template: TestCaseTemplate):
    # TODO: Make implementation of `make_tests_from_template` function.
    ...
