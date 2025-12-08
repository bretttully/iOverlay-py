"""CLI entry point for the i_overlay fuzzer.

Usage:
    python -m tests._fuzzer --runs 1000 --workers 8
    python -m tests._fuzzer --seed 12345  # Reproduce a specific seed
    python -m tests._fuzzer --generator spots --runs 100
    python -m tests._fuzzer --test-rust fuzzer_failures/fuzzer-spots-12.json
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

from .generators import (
    RandomCenterTargetsGenerator,
    RandomPolyGenerator,
    RandomPolygonsGenerator,
    RandomRadiusTargetsGenerator,
    RandomSpotsGenerator,
)
from .runner import (
    TestCase,
    generate_test_case,
    run_fuzzer,
    save_failure_report,
    test_rust_implementation,
)

GENERATORS = {
    "spots": RandomSpotsGenerator,
    "center_targets": RandomCenterTargetsGenerator,
    "radius_targets": RandomRadiusTargetsGenerator,
    "random_polygons": RandomPolygonsGenerator,
}


def reproduce_seed(generator_name: str, seed: int, verbose: bool = True) -> int:
    """Reproduce a specific seed for debugging."""
    generator_cls = GENERATORS.get(generator_name)
    if generator_cls is None:
        print(f"Unknown generator: {generator_name}", file=sys.stderr)
        print(f"Available: {', '.join(GENERATORS.keys())}", file=sys.stderr)
        return 1

    generator = generator_cls()
    test_case = TestCase(generator, seed)

    if verbose:
        print(f"Reproducing seed {seed} with generator {generator_name}")
        print(f"Subject shapes: {len(test_case.subject)}")
        print(f"Clip shapes: {len(test_case.clip)}")
        print()

    df = test_case.time_all()
    errors = df[df.error.notna()]

    if len(errors) == 0:
        print("All tests passed!")
        return 0

    print(f"Found {len(errors)} errors:")
    for _, row in errors.iterrows():
        print(f"  {row['function']}: {row['error']}")

    print()
    print("--- Generated Test Case ---")
    print(generate_test_case(generator, seed, str(errors.iloc[0]["error"])))
    print("----------------------------")

    return 1


def _run_full_fuzzer(args: argparse.Namespace) -> int:
    """Run full fuzzer across generators."""
    generators_to_run = (
        list(GENERATORS.items()) if args.generator == "all" else [(args.generator, GENERATORS[args.generator])]
    )

    all_failures: list[tuple[RandomPolyGenerator, int, pd.DataFrame]] = []

    for _name, generator_cls in generators_to_run:
        generator = generator_cls()
        df = run_fuzzer(
            generator,
            n_procs=args.workers,
            n_tests=args.runs,
            verbose=not args.quiet,
        )

        errors = df[df.error.notna()]
        if len(errors) > 0:
            failing_seeds = errors["seed"].unique()
            if not args.quiet:
                print(f"  Failing seeds: {failing_seeds}")

            for seed in failing_seeds:
                seed_errors = errors[errors["seed"] == seed]
                filepath = save_failure_report(generator, seed, seed_errors, args.output_dir)
                if not args.quiet:
                    print(f"  Saved: {filepath}")
                all_failures.append((generator, seed, seed_errors))

    if args.generate_tests and all_failures:
        print("\n--- Generated Test Cases ---")
        for generator, seed, errors in all_failures:
            print(generate_test_case(generator, seed, str(errors.iloc[0]["error"])))
        print("-----------------------------")

    return 1 if all_failures else 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Fuzz tester for i_overlay boolean operations")
    parser.add_argument(
        "--runs",
        type=int,
        default=None,
        help="Number of test iterations (default: 10 * CPU count)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes (default: CPU count)",
    )
    parser.add_argument(
        "--generator",
        type=str,
        default="all",
        choices=["all", *list(GENERATORS.keys())],
        help="Generator to use (default: all)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Specific seed to reproduce (runs single test)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("fuzzer_failures"),
        help="Directory for failure reports",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    parser.add_argument(
        "--generate-tests",
        action="store_true",
        help="Generate pytest test cases for failures",
    )
    parser.add_argument(
        "--test-rust",
        type=Path,
        default=None,
        metavar="JSON_FILE",
        help="Test a failure JSON against raw Rust implementation",
    )

    args = parser.parse_args()

    # Test against Rust implementation
    if args.test_rust is not None:
        if not args.test_rust.exists():
            print(f"Error: File not found: {args.test_rust}", file=sys.stderr)
            return 1
        success, output = test_rust_implementation(args.test_rust)
        print(output)
        return 0 if success else 1

    # Reproduce specific seed
    if args.seed is not None:
        if args.generator == "all":
            print("Error: --seed requires a specific --generator", file=sys.stderr)
            return 1
        return reproduce_seed(args.generator, args.seed, verbose=not args.quiet)

    # Run full fuzzer
    return _run_full_fuzzer(args)


if __name__ == "__main__":
    sys.exit(main())
