# Example: Makefile autograder

A complete grader for a C Makefile project.

## Assignment spec

Students submit:
- `Makefile` — builds a `wordcount` binary
- `wordcount.c` — implementation

The binary reads lines from stdin and prints word count per line plus a total.

## Score breakdown

| Component | Points |
|-----------|--------|
| Files present | 0 (gate) |
| Build | 15 |
| Correctness | 75 |
| No memory leaks (extra credit) | +10 |
| **Total** | **90 + 10 EC** |

## Full autograder

```python
# autograder.py
from pathlib import Path

import lograder.output.layout.process.executable
import lograder.output.layout.project.simple_project
import lograder.output.layout.test.output_compare
import lograder.output.layout.test.valgrind

from lograder.pipeline.config import config
from lograder.pipeline.input.local_directory import LocalDirectory
from lograder.pipeline.check.project.simple_project import make_simple_manifest_checker
from lograder.pipeline.build.makefile import MakefileBuild
from lograder.pipeline.build.prebuilt import PrebuiltArtifacts
from lograder.pipeline.types.artifacts import FileArtifact
from lograder.pipeline.test.output_compare import OutputCompareTest, OutputCompareCase
from lograder.pipeline.test.valgrind import ValgrindTest, ValgrindCase
from lograder.pipeline.score import (
    AllOrNothingScorer, TestCaseScorer, GimmeConfig, GradescopeConfig,
)
from lograder.pipeline.pipeline import Pipeline

# ── Manifest ──────────────────────────────────────────────────────────────────

make_simple_manifest_checker(
    "wordcount",
    required_files=["Makefile", "wordcount.c"],
)

# ── Test cases ────────────────────────────────────────────────────────────────

OUTPUT_CASES = [
    OutputCompareCase(
        name="empty",
        args=[],
        stdin=b"",
        expected_stdout="total: 0\n",
    ),
    OutputCompareCase(
        name="single_word",
        args=[],
        stdin=b"hello\n",
        expected_stdout="line 1: 1\ntotal: 1\n",
    ),
    OutputCompareCase(
        name="multiple_words",
        args=[],
        stdin=b"hello world\nfoo bar baz\n",
        expected_stdout="line 1: 2\nline 2: 3\ntotal: 5\n",
    ),
    OutputCompareCase(
        name="blank_lines",
        args=[],
        stdin=b"hello\n\nworld\n",
        expected_stdout="line 1: 1\nline 2: 0\nline 3: 1\ntotal: 2\n",
    ),
    OutputCompareCase(
        name="whitespace_only",
        args=[],
        stdin=b"   \n\t\n",
        expected_stdout="line 1: 0\nline 2: 0\ntotal: 0\n",
    ),
]

VALGRIND_CASES = [
    ValgrindCase(name="no_leaks", args=[], stdin=b"hello world\n", check_leaks=True),
]

# ── Pipeline ──────────────────────────────────────────────────────────────────

pipeline = Pipeline()
pipeline.add(LocalDirectory())
pipeline.add(MakefileManifestCheck())
pipeline.add(build := MakefileBuild())
# MakefileBuild returns Ok({}) — inject the binary manually
pipeline.add(PrebuiltArtifacts({"wordcount": FileArtifact(path=Path("wordcount"))}))
pipeline.add(tests := OutputCompareTest("wordcount", OUTPUT_CASES))
pipeline.add(vg    := ValgrindTest("wordcount", VALGRIND_CASES))

# ── Scorers ───────────────────────────────────────────────────────────────────

build.scorer = AllOrNothingScorer(15.0, label="Build")
tests.scorer = TestCaseScorer(
    {
        "empty":           10.0,
        "single_word":     15.0,
        "multiple_words":  20.0,
        "blank_lines":     15.0,
        "whitespace_only": 15.0,
    },
    gimme=GimmeConfig(min_pass_fraction=0.25, points=15.0),
    label="Correctness",
)
vg.scorer = AllOrNothingScorer(0.0, extra_credit=10.0, label="No memory leaks")

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with config(root_directory=Path("/autograder/submission"), executable_timeout=30.0):
        score = pipeline()

    score.write_results_json(config=GradescopeConfig(visibility="visible"))
```

## Notes

`MakefileBuild` runs `make` in the submission directory. It does not currently parse the Makefile to discover built targets, so you must use `PrebuiltArtifacts` to tell lograder where the binary is.

The `path` in `FileArtifact(path=Path("wordcount"))` is relative to `config().root_directory` (the submission directory), so this assumes `make` writes `wordcount` to the root of the submission.

If your Makefile writes to a different location:

```python
pipeline.add(PrebuiltArtifacts({
    "wordcount": FileArtifact(path=Path("bin/wordcount")),
}))
```

## Gradescope `setup.sh`

```bash
#!/usr/bin/env bash
apt-get update -qq
apt-get install -y gcc make valgrind python3 python3-pip
pip3 install lograder
```
