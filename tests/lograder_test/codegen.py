from __future__ import annotations
from typing import List, Literal
import random
from pydantic import BaseModel, Field
from unittest import case

TestType = Literal[
    'blank',
    'basic-pass-check',
    'basic-fail-check',
    'basic-pass-require',
    'basic-fail-require',
    'chain-pass-check',
    'chain-partial-check',
    'chain-fail-check',
    'chain-pass-require',
    'chain-partial-require',
    'chain-fail-require',
]

class Catch2TestBody(BaseModel):
    code: List[str]
    num_tests: int
    num_pass: int

class Catch2Test:

    def __init__(self, success: bool, subtests: List[Catch2Test]):
        self.success = True
        self.subtests = subtests

    def generate_snippet(self, test_type: TestType) -> Catch2TestBody:
        match test_type:
            case 'basic-pass-check':
                a = random.randint(-2_147_483_648, 2_147_483_647)
                return Catch2TestBody(
                    code=[f"CHECK({a} == {a});"],
                    num_tests=1,
                    num_pass=1
                )
            case 'basic-fail-check':
                a, b = random.sample(range(-2_147_483_648, 2_147_483_647), k=2)
                return Catch2TestBody(
                    code=[f"CHECK({a} == {b});"],
                    num_tests=1,
                    num_pass=0
                )
            case 'basic-pass-require':
                a = random.randint(-2_147_483_648, 2_147_483_647)
                return Catch2TestBody(
                    code=[f"REQUIRE({a} == {a});"],
                    num_tests=1,
                    num_pass=1
                )
            case 'basic-fail-require':
                a, b = random.sample(range(-2_147_483_648, 2_147_483_647), k=2)
                return Catch2TestBody(
                    code=[f"REQUIRE({a} == {b});"],
                    num_tests=1,
                    num_pass=0
                )
            case 'chain-pass-check':
                n_lines = random.randint(2, 32)
                code = [self.generate_snippet('basic-pass-check').code[0] for _ in range(n_lines)]
                return Catch2TestBody(
                    code=code,
                    num_tests=n_lines,
                    num_pass=n_lines
                )
            case 'chain-fail-check':
                n_lines = random.randint(2, 32)
                code = [self.generate_snippet('basic-fail-check').code[0] for _ in range(n_lines)]
                return Catch2TestBody(
                    code=code,
                    num_tests=n_lines,
                    num_pass=0
                )
            case 'chain-partial-check':
                n_lines = random.randint(2, 32)
                n_success = random.randint(1, n_lines-1)
                code = [self.generate_snippet('basic-fail-check').code[0] for _ in range(n_lines-n_success)] + \
                    [self.generate_snippet('basic-pass-check').code[0] for _ in range(n_success)]
                random.shuffle(code)
                return Catch2TestBody(
                    code=code,
                    num_tests=n_lines,
                    num_pass=n_success
                )
            case 'chain-pass-require':
                n_lines = random.randint(2, 32)
                code = [self.generate_snippet('basic-pass-require').code[0] for _ in range(n_lines)]
                return Catch2TestBody(
                    code=code,
                    num_tests=n_lines,
                    num_pass=n_lines
                )
            case 'chain-fail-require':
                n_lines = random.randint(2, 32)
                code = [self.generate_snippet('basic-fail-require').code[0] for _ in range(n_lines)]
                return Catch2TestBody(
                    code=code,
                    num_tests=1,
                    num_pass=0
                )
            case 'chain-partial-require':
                n_lines = random.randint(2, 32)
                n_success = random.randint(1, n_lines - 1)
                indices = list(range(n_lines))
                code = [self.generate_snippet('basic-fail-require').code[0] for _ in range(n_lines - n_success)] + \
                       [self.generate_snippet('basic-pass-require').code[0] for _ in range(n_success)]

                random.shuffle(indices)
                indices = [i < n_lines - n_success for i in indices]
                code = [code[i] for i in indices]

                return Catch2TestBody(
                    code=code,
                    num_tests=indices.index(True) + 1,
                    num_pass=indices.index(True)
                )
            case _:
                return Catch2TestBody(
                    code=[],
                    num_tests=0,
                    num_pass=0
                )

    def __str__(self) -> str:
        pass
