# `lograder`: A Gradescope Autograder API

----
This project just serves to standard different kinds of tests
that can be run on student code for the Gradescope autograder.
Additionally, this project was developed for the **University
of Florida's Fall 2025 COP3504C** (*Advanced Programming 
Fundamentals*), taught by Michael Link. However, you are
completely free to use, remix, refactor, and abuse this code
as much as you like.

----
## Features
There are a few types of tests that we support:

----

### C++ Complete Project with [I/O Comparison](#output-comparison)

#### Build from C++ Source (*WIP*)

#### Build using CMake (*WIP*)

#### Build using Makefile (*WIP*)

----

### C++ Catch2 Unit Testing (*WIP*)

----

### Python Complete Project with [I/O Comparison](#output-comparison)

#### Run project from `main.py` (*WIP*)

#### Run project from `pyproject.toml` (*WIP*)

----

### Python pytest Unit Testing (*WIP*)

----

## Output Comparison

### Compare from Files (*WIP*)

If you have a larger test, it would be very convenient to
read files for input and output. Luckily, there's just the
method to do so:

```py
from typing import Sequence, Optional
from os import PathLike
from lograder.tests import make_tests_from_files

FilePath = str | bytes | PathLike[str] | PathLike[bytes]

# `make_tests_from_files` has the following signature.
def make_tests_from_files(
        *,  # kwargs-only; to avoid confusion with argument sequence.
        names: Sequence[str],
        inputs: Sequence[FilePath],
        expected_outputs: Sequence[FilePath],
        weights: Optional[Sequence[float]] = None # Defaults to equal-weight.
): ...

# Here's an example of how you'd use the above method:
make_tests_from_files(
    names=["Test Case 1", "Test Case 2"],
    inputs=["test/inputs/input1.txt", "test/inputs/input2.txt"],
    expected_outputs=["test/inputs/output1.txt", "test/inputs/output2.txt"]
)
```

### Compare from Template (*WIP*)

Finally, sometimes the test-cases might be very long but 
very repetitive. You can use `make_tests_from_template` 
and pass a `TestCaseTemplate` object and ...

```py
from typing import Sequence, Optional
from os import PathLike
from lograder.tests import make_tests_from_template, TestCaseTemplate

FilePath = str | bytes | PathLike[str] | PathLike[bytes]

# Here's the signature of a `TemplateSubstitution`
class TemplateSubstitution:
    def __init__(self, *args, **kwargs):
        # Stores args and kwargs to pass to str.format(...) later.
        ...
TSub = TemplateSubstitution  # Here's an alias that's quicker to type.
    
# Here's the signature of a `TestCaseTemplate`
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
        # +=====================================================================================+
        # | Validation Rules                                                                    |
        # +=====================================================================================+
        #   * If `inputs` is specified, all other `input_*` parameters must be left unspecified.
        #   * Same thing with `expected_outputs`.
        #   * If `inputs` is not specified, you must specify either (mutually exclusive) 
        #     `input_template_file` or `input_template_str` that follows a typical python
        #     format string, and you must specify `input_substitutions`.
        #   * Same thing with `expected_output_template_file`, `expected_output_template_str`, 
        #     and `expected_output_substitutions`
        ...

# Here's an example of how you would use TestCaseTemplate
test_suite_1 = TestCaseTemplate(
    inputs=["A", "B", "C"],  # Three (3) Total Cases
    expected_output_template_str="{}, {kwarged}, {}",
    expected_output_substitutions = [
        TSub(1.0, 2.0, kwarged="middle-arg-1"),  # Case 1 Substitutions
        TSub(2.0, 5.0, kwarged="middle-arg-2"),  # Case 2 Substitutions
        TSub(7.0, 6.0, kwarged="middle-arg-3"),  # Case 3 Substitutions
    ]
)
make_tests_from_template(test_suite_1)  # remember to construct the tests!

```

### Compare from Python Generator/Iterable (*WIP*)

Sometimes, you want to generate a ton of test-cases (especially
small test-cases), and it would be incredibly waste to have thousands
of single-line files. You can create a python generator function that
follows either the following `Protocol` or `TypedDict`.

```py
from typing import Protocol, TypedDict, Generator, NotRequired
from lograder.tests import make_tests_from_generator

# Your generator may return objects following the protocol...
class TestCaseProtocol(Protocol):
    def get_name(self): ...
    def get_input(self): ...
    def get_expected_output(self): ...
    def get_weight(self): ...

# ... or you can directly return a dict with the following keys.
class TestCaseDict(TypedDict):
    name: str
    input: str
    expected_output: str
    weight: NotRequired[float]  # Defaults to 1.0, a.k.a. equal-weight.

# Here's an example of the syntax as well as the required 
# signature of such a method:
@make_tests_from_generator
def test_suite_1() -> Generator[TestCaseProtocol | TestCaseDict, None, None]:
    pass
```



