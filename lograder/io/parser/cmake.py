from ..file_operations import is_default_target

def get_student_targets(cmake_help_output: str) -> list[str]:
    lines = cmake_help_output.splitlines()
    lines = [line[4:] for line in lines if line.startswith('... ')]
    lines = [line for line in lines if not is_default_target(line)]
    return lines
