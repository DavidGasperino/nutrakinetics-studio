from __future__ import annotations

import importlib
import runpy
import subprocess
import sys
from pathlib import Path


def test_canonical_package_import_smoke() -> None:
    module = importlib.import_module("nutrakinetics_studio.simulation")
    assert hasattr(module, "run_simulation")


def test_models_shim_import_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    try:
        module = importlib.import_module("models.simulation")
        assert hasattr(module, "run_simulation")
    finally:
        sys.path.pop(0)


def test_streamlit_entrypoint_imports_package_runner() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    loaded = runpy.run_path(str(repo_root / "app" / "main.py"), run_name="__test__")

    assert "run_app" in loaded
    assert callable(loaded["run_app"])
    assert loaded["run_app"].__module__ == "nutrakinetics_studio.web.streamlit_app"


def test_fit_interactions_help_runs_without_pythonpath_bootstrap() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, str(repo_root / "scripts" / "fit_interactions.py"), "--help"]
    completed = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=False)

    assert completed.returncode == 0
    assert "Fit supplement interaction coefficients" in completed.stdout
