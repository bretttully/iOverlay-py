"""Test runner for fuzzing i_overlay boolean operations.

This module provides the TestCase and runner infrastructure for
executing fuzz tests across multiple CPU cores.
"""

from __future__ import annotations

import concurrent.futures
import dataclasses
import json
import os
from pathlib import Path
import re
import subprocess
import time
from typing import TYPE_CHECKING

import pandas as pd
import shapely
import shapely.geometry
from shapely.validation import explain_validity

from i_overlay import (
    FillRule,
    FloatOverlayGraph,
    OverlayRule,
    overlay,
)

from .generators import RandomPolyGenerator

if TYPE_CHECKING:
    pass

# Type aliases
Point = tuple[float, float]
Contour = list[Point]
Shape = list[Contour]
Shapes = list[Shape]


def _close_ring(ring: Contour) -> Contour:
    """Close a ring if not already closed."""
    if ring[0] != ring[-1]:
        return [*ring, ring[0]]
    return ring


def _convert_shape_to_polygon(shape: Shape) -> shapely.geometry.Polygon | None:
    """Convert a single shape to a shapely Polygon."""
    if not shape:
        return None
    exterior = shape[0]
    if len(exterior) < 3:
        return None
    exterior = _close_ring(exterior)
    holes = [_close_ring(hole) for hole in shape[1:] if len(hole) >= 3]
    try:
        poly = shapely.geometry.Polygon(exterior, holes or None)
        return poly if not poly.is_empty else None
    except Exception:
        return None


def shapes_to_shapely(shapes: Shapes) -> shapely.geometry.MultiPolygon:
    """Convert i_overlay Shapes to shapely MultiPolygon."""
    polygons = [poly for shape in shapes if (poly := _convert_shape_to_polygon(shape)) is not None]
    if not polygons:
        return shapely.geometry.MultiPolygon()
    return shapely.geometry.MultiPolygon(polygons)


@dataclasses.dataclass(frozen=True)
class TestCase:
    """A single test case with subject and clip shapes.

    Generates two sets of shapes using the generator with different seeds,
    then provides methods to test all overlay operations.
    """

    generator: RandomPolyGenerator
    seed: int
    subject: Shapes = dataclasses.field(init=False)
    clip: Shapes = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        # Use seed for subject, seed + large offset for clip
        object.__setattr__(self, "subject", self.generator(self.seed))
        object.__setattr__(self, "clip", self.generator(self.seed + 1_000_000_000))

    def _validate_result(self, result: Shapes) -> str | None:
        """Validate the result and return error message if invalid."""
        try:
            geom = shapes_to_shapely(result)
            if not geom.is_valid:
                return f"Invalid geometry: {explain_validity(geom)}"
            return None
        except Exception as e:
            return f"Validation error: {e}"

    def _run_overlay(self, overlay_rule: OverlayRule, fill_rule: FillRule) -> tuple[Shapes | None, str | None]:
        """Run an overlay operation and return result with any error."""
        try:
            result = overlay(self.subject, self.clip, overlay_rule, fill_rule)
            error = self._validate_result(result)
            return result, error
        except Exception as e:
            return None, f"{type(e).__name__}: {e}"

    def _run_graph_extract(
        self, graph: FloatOverlayGraph, overlay_rule: OverlayRule
    ) -> tuple[Shapes | None, str | None]:
        """Extract shapes from graph and return result with any error."""
        try:
            result = graph.extract_shapes(overlay_rule)
            error = self._validate_result(result)
            return result, error
        except Exception as e:
            return None, f"{type(e).__name__}: {e}"

    # Individual test methods for different overlay rules and fill rules
    def overlay_union_evenodd(self) -> Shapes | None:
        result, _ = self._run_overlay(OverlayRule.Union, FillRule.EvenOdd)
        return result

    def overlay_union_nonzero(self) -> Shapes | None:
        result, _ = self._run_overlay(OverlayRule.Union, FillRule.NonZero)
        return result

    def overlay_intersect_evenodd(self) -> Shapes | None:
        result, _ = self._run_overlay(OverlayRule.Intersect, FillRule.EvenOdd)
        return result

    def overlay_intersect_nonzero(self) -> Shapes | None:
        result, _ = self._run_overlay(OverlayRule.Intersect, FillRule.NonZero)
        return result

    def overlay_difference_evenodd(self) -> Shapes | None:
        result, _ = self._run_overlay(OverlayRule.Difference, FillRule.EvenOdd)
        return result

    def overlay_difference_nonzero(self) -> Shapes | None:
        result, _ = self._run_overlay(OverlayRule.Difference, FillRule.NonZero)
        return result

    def overlay_xor_evenodd(self) -> Shapes | None:
        result, _ = self._run_overlay(OverlayRule.Xor, FillRule.EvenOdd)
        return result

    def overlay_xor_nonzero(self) -> Shapes | None:
        result, _ = self._run_overlay(OverlayRule.Xor, FillRule.NonZero)
        return result

    def time_all(self) -> pd.DataFrame:
        """Run all test methods and collect timing and error information."""
        overlay_rules = [
            OverlayRule.Union,
            OverlayRule.Intersect,
            OverlayRule.Difference,
            OverlayRule.Xor,
        ]
        fill_rules = [
            FillRule.EvenOdd,
            FillRule.NonZero,
            FillRule.Positive,
            FillRule.Negative,
        ]

        results = []

        # Test direct overlay calls
        for overlay_rule in overlay_rules:
            for fill_rule in fill_rules:
                func_name = f"overlay_{overlay_rule}_{fill_rule}"
                t0 = time.monotonic()
                try:
                    _result, error = self._run_overlay(overlay_rule, fill_rule)
                except Exception as e:
                    error = f"{type(e).__name__}: {e}"
                elapsed = time.monotonic() - t0

                results.append(
                    {
                        "generator": self.generator.name(),
                        "seed": self.seed,
                        "function": func_name,
                        "error": error,
                        "time_ms": 1000 * elapsed,
                    }
                )

        # Test FloatOverlayGraph
        for fill_rule in fill_rules:
            # Build graph
            graph_func = f"graph_build_{fill_rule}"
            t0 = time.monotonic()
            graph = None
            graph_error = None
            try:
                graph = FloatOverlayGraph(self.subject, self.clip, fill_rule)
            except Exception as e:
                graph_error = f"{type(e).__name__}: {e}"
            elapsed = time.monotonic() - t0

            results.append(
                {
                    "generator": self.generator.name(),
                    "seed": self.seed,
                    "function": graph_func,
                    "error": graph_error,
                    "time_ms": 1000 * elapsed,
                }
            )

            # Extract from graph
            if graph is not None:
                for overlay_rule in overlay_rules:
                    extract_func = f"graph_extract_{overlay_rule}_{fill_rule}"
                    t0 = time.monotonic()
                    try:
                        _, error = self._run_graph_extract(graph, overlay_rule)
                    except Exception as e:
                        error = f"{type(e).__name__}: {e}"
                    elapsed = time.monotonic() - t0

                    results.append(
                        {
                            "generator": self.generator.name(),
                            "seed": self.seed,
                            "function": extract_func,
                            "error": error,
                            "time_ms": 1000 * elapsed,
                        }
                    )

        return pd.DataFrame(results)


@dataclasses.dataclass(frozen=True)
class FuzzRunner:
    """Runs fuzz tests for a generator."""

    generator: RandomPolyGenerator

    def __call__(self, seed: int) -> pd.DataFrame:
        """Run all tests for a single seed."""
        return TestCase(self.generator, seed).time_all()


def run_fuzzer(
    generator: RandomPolyGenerator,
    n_procs: int | None = None,
    n_tests: int | None = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """Run the fuzzer with multiple processes.

    Args:
        generator: The polygon generator to use.
        n_procs: Number of processes (default: CPU count).
        n_tests: Number of test iterations (default: 10 * CPU count).
        verbose: Whether to print progress.

    Returns:
        DataFrame with all test results.
    """
    if n_procs is None:
        n_procs = os.cpu_count() or 1
    if n_tests is None:
        n_tests = 10 * n_procs

    if verbose:
        print(f"Running fuzzer: generator={generator.name()}, procs={n_procs}, tests={n_tests}")

    runner = FuzzRunner(generator)
    t0 = time.monotonic()

    with concurrent.futures.ProcessPoolExecutor(max_workers=min(n_procs, n_tests)) as pool:
        dfs = list(pool.map(runner, range(n_tests)))

    elapsed = time.monotonic() - t0
    df = pd.concat(dfs, ignore_index=True)

    if verbose:
        n_errors = df.error.notna().sum()
        print(f"Completed {n_tests} tests in {elapsed:.2f}s ({n_errors} errors)")

    return df


def save_failure_report(
    generator: RandomPolyGenerator,
    seed: int,
    error_df: pd.DataFrame,
    output_dir: Path | None = None,
) -> Path:
    """Save a failure report for debugging.

    Args:
        generator: The generator used.
        seed: The failing seed.
        error_df: DataFrame of errors for this seed.
        output_dir: Output directory (default: fuzzer_failures/).

    Returns:
        Path to the saved report.
    """
    if output_dir is None:
        output_dir = Path("fuzzer_failures")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Regenerate the test case
    test_case = TestCase(generator, seed)

    # Collect failing results
    failing_results: dict[str, Shapes] = {}
    for _, row in error_df.iterrows():
        func_name = row["function"]
        # Parse overlay_rule and fill_rule from function name
        # Format: "overlay_OverlayRule.{rule}_FillRule.{rule}" or "graph_extract_..."
        if func_name.startswith("overlay_") or func_name.startswith("graph_extract_"):
            # Extract OverlayRule.X and FillRule.Y from the function name
            match = re.search(r"OverlayRule\.(\w+)_FillRule\.(\w+)", func_name)
            if match:
                overlay_name = match.group(1)
                fill_name = match.group(2)
                try:
                    overlay_rule = getattr(OverlayRule, overlay_name)
                    fill_rule = getattr(FillRule, fill_name)
                    result = overlay(test_case.subject, test_case.clip, overlay_rule, fill_rule)
                    # Only save unique results (same overlay+fill combo)
                    key = f"{overlay_name}_{fill_name}"
                    if key not in failing_results:
                        failing_results[key] = result
                except (AttributeError, Exception):
                    pass  # Skip if we can't reproduce

    report = {
        "generator": generator.name(),
        "seed": int(seed),  # Ensure native int for JSON serialization
        "subject": test_case.subject,
        "clip": test_case.clip,
        "errors": error_df.to_dict(orient="records"),
        "failing_results": failing_results,
    }

    filepath = output_dir / f"fuzzer-{generator.name()}-{seed}.json"
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2, default=str)  # default=str for any non-serializable types

    return filepath


def generate_test_case(generator: RandomPolyGenerator, seed: int, error: str) -> str:
    """Generate a pytest test case from a failure.

    Args:
        generator: The generator used.
        seed: The failing seed.
        error: The error message.

    Returns:
        Python code for a test function.
    """
    test_case = TestCase(generator, seed)
    subject_str = repr(test_case.subject)
    clip_str = repr(test_case.clip)

    return f'''def test_fuzzer_{generator.name()}_{seed}():
    """Regression test from fuzzer failure.

    Generator: {generator.name()}
    Seed: {seed}
    Error: {error}
    """
    from i_overlay import FillRule, OverlayRule, overlay

    subject = {subject_str}
    clip = {clip_str}

    # Test all overlay rules
    for overlay_rule in [OverlayRule.Union, OverlayRule.Intersect, OverlayRule.Difference, OverlayRule.Xor]:
        for fill_rule in [FillRule.EvenOdd, FillRule.NonZero]:
            result = overlay(subject, clip, overlay_rule, fill_rule)
            assert isinstance(result, list)
'''


def test_rust_implementation(json_path: Path) -> tuple[bool, str]:
    """Test a fuzzer failure against the raw Rust implementation.

    This runs the `test_fuzzer_failure` binary to determine if a failure
    is in the Python bindings or the upstream Rust library.

    Args:
        json_path: Path to the fuzzer failure JSON file.

    Returns:
        Tuple of (success, output) where success is True if all Rust tests pass.
    """
    # Try to find the binary
    binary_paths = [
        Path("target/release/test_fuzzer_failure"),
        Path("target/debug/test_fuzzer_failure"),
    ]

    binary = None
    for p in binary_paths:
        if p.exists():
            binary = p
            break

    if binary is None:
        return False, "Binary not found. Run: cargo build --bin test_fuzzer_failure"

    try:
        result = subprocess.run(
            [str(binary), str(json_path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Test timed out after 60 seconds"
    except Exception as e:
        return False, f"Error running binary: {e}"
