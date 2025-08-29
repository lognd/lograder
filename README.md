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
# Project Builders

----

### C++ Complete Project with [I/O Comparison](#output-comparison)

#### Build from C++ Source (*WIP*)
To build from source, you will need to import the C++
`CxxSourceBuilder`. The executable will be randomly
named and put in either a build directory, if the student
has one (`./build`) or the project root directory (`./`).
```py
from lograder.builder import CxxSourceBuilder
from lograder.output import AssignmentSummary

# Note that when you make a test, it's automatically
# registered with the `lograder.tests.registry.TestRegistry`

assignment = CxxSourceBuilder(project_root="/autograder/submission")
preprocessor_results = assignment.preprocess()
build_results = assignment.build()
runtime_results = assignment.run_tests()

summary = AssignmentSummary(
    preprocessor_output = preprocessor_results.get_output(),
    build_output = build_results.get_output(),
    build_info = build_results.get_info(),
    runtime_summary = runtime_results.get_summary(),
    test_cases = runtime_results.get_test_cases()
)
```

#### Build using CMake (*WIP*)
To build from a `CMakeLists.txt`, you will need to import the C++
`CMakeBuilder`. This method will automatically run a breadth-first
search starting in the project root directory (`./`) and "lock on"
the first (i.e. the file in the highest-level) `CMakeLists.txt` that
it finds. If it can't find a `CMakeLists.txt`, it will raise an error.

Additionally, the program will look for the following targets first:
`main`, `build`, and `demo`. Afterward, it will search for any target
that doesn't match: `all`, `install`, `test`, `package`, `package_source`,
`edit_cache`, `rebuild_cache`, `clean`, `help`, `ALL_BUILD`, `ZERO_CHECK`,
`INSTALL`, `RUN_TESTS`, and `PACKAGE`, and run the first target that it
finds. If it can't find a valid target, it will raise an error.

```py
from lograder.builder import CMakeBuilder
from lograder.output import AssignmentSummary

# Note that when you make a test, it's automatically
# registered with the `lograder.tests.registry.TestRegistry`

assignment = CMakeBuilder(project_root="/autograder/submission")
preprocessor_results = assignment.preprocess()
build_results = assignment.build()
runtime_results = assignment.run_tests()

summary = AssignmentSummary(
    preprocessor_output = preprocessor_results.get_output(),
    build_output = build_results.get_output(),
    build_info = build_results.get_info(),
    runtime_summary = runtime_results.get_summary(),
    test_cases = runtime_results.get_test_cases()
)
```
----

### C++ Catch2 Unit Testing (*WIP*)

----

### Python Complete Project with [I/O Comparison](#output-comparison)

#### Run project from `main.py` (*WIP*)

#### Run project from `pyproject.toml` (*WIP*)

----

### Python pytest Unit Testing (*WIP*)

----

### Makefile Complete Project with [I/O Comparison](#output-comparison) (*WIP*)

To build from a `Makefile`, you will need a `MakefileBuilder`. It follows
the same general idea as the `CMakeBuilder` except that it searches for
`Makefile` instead of `CMakeLists.txt`. Additionally, `MakefileBuilder`
will just run the default `make`.

```py
from lograder.builder import MakefileBuilder
from lograder.output import AssignmentSummary

# Note that when you make a test, it's automatically
# registered with the `lograder.tests.registry.TestRegistry`

assignment = MakefileBuilder(project_root="/autograder/submission")
preprocessor_results = assignment.preprocess()
build_results = assignment.build()
runtime_results = assignment.run_tests()

summary = AssignmentSummary(
    preprocessor_output = preprocessor_results.get_output(),
    build_output = build_results.get_output(),
    build_info = build_results.get_info(),
    runtime_summary = runtime_results.get_summary(),
    test_cases = runtime_results.get_test_cases()
)
```

----
# Test Generation

----

## Output Comparison

### Compare Simple Strings

For the smallest number of tiny test cases, there's no reason
to have an over-bloated mess. You can just use:

```py
from typing import Sequence, Optional, List
from lograder.tests import make_tests_from_strs, ComparisonTest


def make_test_from_strs(
    *,  # kwargs-only; to avoid confusion with argument sequence.
    names: Sequence[str],
    inputs: Sequence[str],
    expected_outputs: Sequence[str],
    weights: Optional[Sequence[float]] = None,  # Defaults to equal-weight.
) -> List[ComparisonTest]: ...


# Here's an example of how you'd use the above method:
make_tests_from_strs(
    names=["Test Case 1", "Test Case 2"],
    inputs=["stdin-1", "stdin-2"],
    expected_outputs=["stdout-1", "stdout-2"]
)
```

### Compare from Files

If you have a larger test, it would be very convenient to
read files for input and output. Luckily, there's just the
method to do so:

```py
from typing import Sequence, Optional, List
from lograder.tests import make_tests_from_files, FilePath, ComparisonTest


# `make_tests_from_files` has the following signature.
def make_tests_from_files(
    *,  # kwargs-only; to avoid confusion with argument sequence.
    names: Sequence[str],
    input_files: Optional[Sequence[FilePath]] = None,  # `input_files` and `input_strs` mutually exclusive.
    input_strs: Optional[Sequence[str]] = None,
    expected_output_files: Optional[Sequence[FilePath]] = None,  # same with `expected_output_files` and `expected_output_strs`
    expected_output_strs: Optional[Sequence[str]] = None,
    weights: Optional[Sequence[float]] = None,  # Defaults to equal-weight.
) -> List[ComparisonTest]: ...


# Here's an example of how you'd use the above method:
make_tests_from_files(
    names=["Test Case 1", "Test Case 2"],
    input_files=["test/inputs/input1.txt", "test/inputs/input2.txt"],
    expected_output_files=["test/inputs/output1.txt", "test/inputs/output2.txt"]
)
```

### Compare from Template

Finally, sometimes the test-cases might be very long but 
very repetitive. You can use `make_tests_from_template` 
and pass a `TestCaseTemplate` object and ...

```py
from typing import Sequence, Optional
from lograder.tests import make_tests_from_template, TestCaseTemplate, FilePath


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
    expected_output_substitutions=[
        TSub(1.0, 2.0, kwarged="middle-arg-1"),  # Case 1 Substitutions
        TSub(2.0, 5.0, kwarged="middle-arg-2"),  # Case 2 Substitutions
        TSub(7.0, 6.0, kwarged="middle-arg-3"),  # Case 3 Substitutions
    ]
)
make_tests_from_template(
    ["Test 1", "Test 2", "Test 3"],
    test_suite_1
)  # remember to construct the tests!

```

### Compare from Python Generator/Iterable

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


# Notice that TestCaseProtocol defaults to equal-weights
class WeightedTestCaseProtocol(TestCaseProtocol):
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
def test_suite_1() -> Generator[TestCaseProtocol | WeightedTestCaseProtocol | TestCaseDict, None, None]:
    pass

# You'll have to query the `TestRegistry` from `lograder.tests` to access these tests, though.
```



