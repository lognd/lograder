from abc import ABC, abstractmethod

class ResultInterface(ABC):
    @abstractmethod
    def get_successful(self) -> bool:
        ...

class BuilderInterface(ABC):
    @abstractmethod
    def preprocess(self):
        ...
    @abstractmethod
    def build(self):
        ...
    @abstractmethod
    def run(self):
        ...
