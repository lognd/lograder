from ..common.assignment import PreprocessorOutput
from ..common.interface import (
    PreprocessorInterface,
    PreprocessorResults,
)

class IllegalPhrasePreprocessor(PreprocessorInterface):
    def validate(self):
        return True

    def preprocess(self) -> PreprocessorResults:
        return PreprocessorResults(
            output=PreprocessorOutput(commands=[], stdout=[], stderr=[])
        )