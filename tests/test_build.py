from fnmatch import fnmatch
from importlib import import_module
from pathlib import Path
from typing import Callable

IGNORE_DIRS = {
    "__pycache__",
    "build",
    "develop-eggs",
    "dist",
    "downloads",
    "eggs",
    ".eggs",
    "lib",
    "lib64",
    "parts",
    "sdist",
    "var",
    "wheels",
    "share",
    "htmlcov",
    ".tox",
    ".nox",
    ".hypothesis",
    ".pytest_cache",
    "cover",
    "instance",
    ".scrapy",
    "_build",
    ".pybuilder",
    "target",
    ".ipynb_checkpoints",
    "profile_default",
    "__pypackages__",
    "env",
    "venv",
    "ENV",
    "env.bak",
    "venv.bak",
    ".spyderproject",
    ".spyproject",
    ".ropeproject",
    "site",
    ".mypy_cache",
    ".pyre",
    ".pytype",
    "cython_debug",
    ".abstra",
    ".ruff_cache",
    ".pixi",
    ".pdm-build",
    "__marimo__",
}

IGNORE_FILE_GLOBS = {
    "*.py[codz]",
    "*$py.class",
    "*.so",
    "*.egg",
    "*.egg-info",
    "*.manifest",
    "*.spec",
    "*.log",
    "*.mo",
    "*.pot",
    "*.sage.py",
    "*.cover",
    "*.py.cover",
}

IGNORE_FILES = {
    ".Python",
    ".installed.cfg",
    "MANIFEST",
    "pip-log.txt",
    "pip-delete-this-directory.txt",
    ".coverage",
    ".cache",
    "nosetests.xml",
    "coverage.xml",
    "local_settings.py",
    "db.sqlite3",
    "db.sqlite3-journal",
    "ipython_config.py",
    "celerybeat-schedule",
    "celerybeat.pid",
    ".env",
    ".envrc",
    ".pdm-python",
    ".pypirc",
    ".dmypy.json",
    "dmypy.json",
    ".cursorignore",
    ".cursorindexingignore",
}


def should_ignore(path: Path) -> bool:  # Follows basic Python `.gitignore`
    name = path.name

    if path.is_dir():
        if name in IGNORE_DIRS:
            return True

    if name in IGNORE_FILES:
        return True

    for pattern in IGNORE_FILE_GLOBS:
        if fnmatch(name, pattern):
            return True

    return False


def find_project_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "pyproject.toml").exists():
            return p
    raise FileNotFoundError(
        f"Cannot find project root; `pyproject.toml` not found in any of test_file's (`{str(Path(__file__).resolve())}`) parent directories."
    )


def get_project_name() -> str:
    source_directory: Path = find_project_root(Path(__file__).resolve()) / "src"
    python_project_directory: list[Path] = [
        d for d in source_directory.iterdir() if d.is_dir() and not should_ignore(d)
    ]
    if len(python_project_directory) == 0:
        raise Exception(
            f"Project source directory (`{str(source_directory)}`) does not contain project directory."
        )
    elif len(python_project_directory) > 1:
        raise Exception(
            f"Project source directory (`{str(source_directory)}`) contains more than one ({len(python_project_directory)}) project directory."
        )
    return python_project_directory[0].name


def test_build() -> None:
    project_name: str = get_project_name()
    mod = import_module(project_name)
    hello_world: Callable[[], str] = getattr(mod, "hello_world")
    assert hello_world() == f"Hello world from `{project_name}`!"
