"""Tests to verify stubs match runtime using mypy.stubtest."""

from pathlib import Path
import subprocess
import sys


def test_stubtest() -> None:
    """Run mypy.stubtest to verify stubs match runtime."""
    # Find the allowlist file
    allowlist = Path(__file__).parent.parent / "stubtest_allowlist.txt"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy.stubtest",
            "i_overlay",
            "--allowlist",
            str(allowlist),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

    assert result.returncode == 0, f"stubtest failed:\n{result.stdout}\n{result.stderr}"
