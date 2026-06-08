import subprocess
import sys
import types

import PQEnalyzer


def test_version_from_git_returns_git_description(monkeypatch):
    def run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, stdout="v1.2.3\n")

    monkeypatch.setattr(subprocess, "run", run)

    assert PQEnalyzer._version_from_git() == "v1.2.3"


def test_version_from_git_returns_none_when_git_fails(monkeypatch):
    def run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout="")

    monkeypatch.setattr(subprocess, "run", run)

    assert PQEnalyzer._version_from_git() is None


def test_get_version_uses_setuptools_scm_when_package_metadata_is_missing(
        monkeypatch):
    setuptools_scm = types.ModuleType("setuptools_scm")
    setuptools_scm.get_version = lambda **kwargs: "1.2.3"
    monkeypatch.setitem(sys.modules, "setuptools_scm", setuptools_scm)
    monkeypatch.setattr(PQEnalyzer, "version",
                        lambda name: (_ for _ in ()).throw(
                            PQEnalyzer.PackageNotFoundError()))

    assert PQEnalyzer._get_version() == "1.2.3"


def test_get_version_falls_back_to_unknown_when_git_version_fails(
        monkeypatch):
    setuptools_scm = types.ModuleType("setuptools_scm")
    setuptools_scm.get_version = lambda **kwargs: (_ for _ in ()).throw(
        RuntimeError("version unavailable"))
    monkeypatch.setitem(sys.modules, "setuptools_scm", setuptools_scm)
    monkeypatch.setattr(PQEnalyzer, "version",
                        lambda name: (_ for _ in ()).throw(
                            PQEnalyzer.PackageNotFoundError()))
    monkeypatch.setattr(PQEnalyzer, "_version_from_git",
                        lambda: (_ for _ in ()).throw(
                            RuntimeError("git unavailable")))

    assert PQEnalyzer._get_version() == "0+unknown"
