from __future__ import annotations

from functools import lru_cache
from pathlib import Path


def _is_repo_root(path: Path) -> bool:
    return (path / "pyproject.toml").is_file() and (path / "config").is_dir()


@lru_cache(maxsize=1)
def repo_root() -> Path:
    file_path = Path(__file__).resolve()
    for candidate in (file_path, *file_path.parents):
        if _is_repo_root(candidate):
            return candidate

    # Editable installs should resolve to <repo>/src/nutrakinetics_studio/paths.py.
    fallback = file_path.parents[2]
    if _is_repo_root(fallback):
        return fallback

    raise FileNotFoundError("Could not locate repository root with pyproject.toml and config/.")


def config_file(filename: str) -> Path:
    return repo_root() / "config" / filename


def data_file(*parts: str) -> Path:
    return repo_root() / "data" / Path(*parts)
