from importlib.metadata import metadata
from pathlib import Path


def hello_world() -> str:
    return f"Hello world from `{metadata(Path(__file__).parent.name)['Name']}`!"
