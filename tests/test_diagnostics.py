"""Verify the public diagnostic output without requiring game access."""

import json
import subprocess
import sys

from isaac_threrisaifuture.cli import doctor


def test_doctor_reports_environment_without_claiming_game_support() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "isaac_threrisaifuture.cli", "doctor"],
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)
    assert report["game_integration"] == "observer_implemented_runtime_unverified"
    assert report["packages"]["gymnasium"]
    assert report["packages"]["sb3-contrib"]


def test_missing_dependency_is_reported_without_crashing(monkeypatch) -> None:
    import importlib.metadata

    real_version = importlib.metadata.version

    def version_with_missing_torch(package: str) -> str:
        if package == "torch":
            raise importlib.metadata.PackageNotFoundError(package)
        return real_version(package)

    monkeypatch.setattr(importlib.metadata, "version", version_with_missing_torch)
    report = doctor()
    assert report["packages"]["torch"] is None
    assert report["packages"]["numpy"]
