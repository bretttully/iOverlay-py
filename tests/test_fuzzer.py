"""Execution tests for i_overlay using random geometry fuzzing.

Run with:
    OVERLAY_FUZZ_TEST_ENABLED=1 pytest tests/test_fuzzer.py -v

Environment variables:
    OVERLAY_FUZZ_TEST_ENABLED: Set to "1" to enable (disabled by default)
    OVERLAY_FUZZ_TEST_NPROC: Number of processes (default: CPU count)
    OVERLAY_FUZZ_TEST_NTESTS: Number of tests per generator (default: 10 * NPROC)
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from ._fuzzer import (
    RandomCenterTargetsGenerator,
    RandomPolygonsGenerator,
    RandomRadiusTargetsGenerator,
    RandomSpotsGenerator,
    run_fuzzer,
)

if TYPE_CHECKING:
    from ._fuzzer import RandomPolyGenerator

generator_types = [
    RandomSpotsGenerator,
    RandomCenterTargetsGenerator,
    RandomRadiusTargetsGenerator,
    RandomPolygonsGenerator,
]


@pytest.mark.skipif(
    os.getenv("OVERLAY_FUZZ_TEST_ENABLED") != "1",
    reason="Only run if OVERLAY_FUZZ_TEST_ENABLED=1",
)
@pytest.mark.parametrize("generator_cls", generator_types)
def test_fuzzer_execution(generator_cls: type[RandomPolyGenerator]) -> None:
    """Run fuzz tests for a generator and verify no errors occur."""
    generator = generator_cls()
    n_procs = int(os.getenv("OVERLAY_FUZZ_TEST_NPROC", str(os.cpu_count() or 1)))
    n_tests = int(os.getenv("OVERLAY_FUZZ_TEST_NTESTS", str(10 * n_procs)))

    assert n_procs > 0
    assert n_tests >= n_procs

    df = run_fuzzer(generator, n_procs=n_procs, n_tests=n_tests, verbose=True)
    error_df = df[df.error.notna()]

    if len(error_df) > 0:
        failing_seeds = error_df["seed"].unique()
        pytest.fail(f"Fuzzer found errors. Failing seeds: {failing_seeds}")
