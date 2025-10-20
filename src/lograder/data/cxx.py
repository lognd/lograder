from typing import List


class CxxConfig:
    DEFAULT_CXX_STANDARD: str = "c++20"
    DEFAULT_CXX_COMPILATION_FLAGS: List[str] = [
        "-Wall",
        "-Wextra",
        "-Wshadow",
        "-Wconversion",
        "-Wsign-conversion",
        "-Wnull-dereference",
        "-Werror=return-type"
    ]
    DEFAULT_CMAKE_COMPILATION_FLAGS: List[str] = []
