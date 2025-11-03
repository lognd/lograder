import os
from pathlib import Path


class PathConfig:
    """Dynamic path resolver for build and grading environments.

    This configuration automatically detects whether it is running inside
    an autograder, CI/CD container, or local workspace, and sets defaults
    accordingly.
    """

    # Default fallback paths
    _DEFAULTS = {
        "root": Path("/autograder"),
        "source": Path("/autograder/source"),
        "submission": Path("/autograder/submission"),
        "results": Path("/autograder/results/results.json"),
    }

    @classmethod
    def detect_environment(cls) -> str:
        """Detects the active environment type."""
        if Path("/autograder").exists():
            return "autograder"
        if os.getenv("CI"):
            return "ci"
        return "local"

    @classmethod
    def resolve(cls, name: str) -> Path:
        """Resolve a path by name, checking environment variables first."""
        env_key = f"{name.upper()}_PATH"
        if env_key in os.environ:
            return Path(os.environ[env_key])
        return cls._DEFAULTS.get(name, Path.cwd())

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------
    @property
    def root(self) -> Path:
        """Root directory of environment (autograder or local)."""
        return self.resolve("root")

    @property
    def source(self) -> Path:
        """Source directory (grader or project)."""
        return self.resolve("source")

    @property
    def submission(self) -> Path:
        """Submission or working directory."""
        return self.resolve("submission")

    @property
    def results(self) -> Path:
        """Result JSON path."""
        return self.resolve("results")

    def summary(self) -> dict[str, Path]:
        """Return all resolved paths."""
        return {
            "root": self.root,
            "source": self.source,
            "submission": self.submission,
            "results": self.results,
        }
