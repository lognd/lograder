import pytest

from lograder import hello_world

@pytest.mark.description('Testing to see if package, `lograder`, built successfully.')
def test_build():
    assert hello_world() == "Hello world! ~from `lograder`!"
