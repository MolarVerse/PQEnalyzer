import subprocess
import sys
from pathlib import Path


def test_cli_version_from_source_checkout():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [sys.executable, "-m", "PQEnalyzer", "--version"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Traceback" not in result.stderr
    assert result.stdout.startswith("PQEnalyzer ")
