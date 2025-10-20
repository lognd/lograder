from .process import FileProcess, Commands, step
from ...data.cxx import CxxConfig

class CxxSourceBuilder(FileProcess):
    commands: Commands = [
        ["g++", *CxxConfig.DEFAULT_CXX_COMPILATION_FLAGS, "${cxx_files}", "-o", "${executable}"]
    ]

class CMakeBuilder(FileProcess):
    commands: Commands = [
        [],
        []
    ]