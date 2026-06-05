# mypy: ignore-errors
from pathlib import Path

import pytest

from lograder.exception import StaffException
from lograder.pipeline.config import (
    EnvironmentConfig,
    config,
    config_from_toml,
    get_config,
)


def test_default_config_root_is_slash():
    cfg = EnvironmentConfig()
    assert cfg.root_directory == Path("/")


def test_get_config_returns_default():
    cfg = get_config()
    assert isinstance(cfg, EnvironmentConfig)


def test_config_context_manager_patches_root(tmp_path):
    with config(root_directory=tmp_path):
        assert get_config().root_directory == tmp_path


def test_config_context_manager_restores_on_exit(tmp_path):
    before = get_config().root_directory
    with config(root_directory=tmp_path):
        pass
    assert get_config().root_directory == before


def test_config_nested_contexts(tmp_path):
    outer = tmp_path / "outer"
    inner = tmp_path / "inner"
    outer.mkdir()
    inner.mkdir()
    with config(root_directory=outer):
        assert get_config().root_directory == outer
        with config(root_directory=inner):
            assert get_config().root_directory == inner
        assert get_config().root_directory == outer


def test_config_invalid_key_raises_staff_exception():
    with pytest.raises(StaffException):
        with config(nonexistent_key=1):
            pass


def test_config_timeout_patched():
    with config(executable_timeout=30.0):
        assert get_config().executable_timeout == 30.0


def test_config_max_workers_patched():
    with config(executable_max_workers=4):
        assert get_config().executable_max_workers == 4


def test_config_from_toml_loads_root_directory(tmp_path):
    toml_file = tmp_path / "config.toml"
    toml_file.write_text(f'root_directory = "{tmp_path}"\n', encoding="utf-8")
    with config_from_toml(toml_file) as cfg:
        assert Path(cfg.root_directory) == tmp_path


def test_config_from_toml_missing_file_raises(tmp_path):
    missing = tmp_path / "nonexistent.toml"
    with pytest.raises(StaffException):
        config_from_toml(missing)
