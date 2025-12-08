#!/usr/bin/env python3
"""
Analysis script to demonstrate OGC validity differences between iOverlay and Shapely.

This script loads a test case that causes iOverlay to produce OGC-invalid output,
compares with Shapely's output, and generates visualizations.

Usage:
    python docs/analyze_validity.py

Requirements:
    pip install shapely matplotlib numpy i_overlay
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import explain_validity, make_valid

from i_overlay import FillRule, OverlayRule, overlay


def load_test_case(json_path: Path) -> tuple[list, list]:
    """Load subject and clip shapes from JSON file."""
    with open(json_path) as f:
        data = json.load(f)

    def convert_shapes(shapes):
        return [[[tuple(pt) for pt in contour] for contour in shape] for shape in shapes]

    return convert_shapes(data["subject"]), convert_shapes(data["clip"])


def shapes_to_shapely(shapes: list) -> MultiPolygon:
    """Convert i_overlay shapes format to Shapely MultiPolygon."""
    polygons = []
    for shape in shapes:
        if not shape:
            continue
        exterior = list(shape[0])
        if len(exterior) < 3:
            continue
        # Close ring if needed
        if exterior[0] != exterior[-1]:
            exterior = exterior + [exterior[0]]
        holes = []
        for hole in shape[1:]:
            if len(hole) >= 3:
                h = list(hole) if hole[0] == hole[-1] else list(hole) + [hole[0]]
                holes.append(h)
        try:
            poly = Polygon(exterior, holes or None)
            if not poly.is_empty:
                polygons.append(poly)
        except Exception:
            pass
    return MultiPolygon(polygons) if polygons else MultiPolygon()


def plot_multipolygon(ax, geom, title: str, highlight_invalid: bool = True):
    """Plot a MultiPolygon or Polygon with optional invalid highlighting."""
    ax.set_title(title)
    ax.set_aspect('equal')

    if isinstance(geom, Polygon):
        geoms = [geom]
    elif isinstance(geom, MultiPolygon):
        geoms = list(geom.geoms)
    else:
        geoms = []

    for poly in geoms:
        is_valid = poly.is_valid

        # Plot exterior
        x, y = poly.exterior.xy
        if highlight_invalid and not is_valid:
            ax.fill(x, y, alpha=0.5, fc='red', ec='darkred', linewidth=1.5)
        else:
            ax.fill(x, y, alpha=0.5, fc='blue', ec='darkblue', linewidth=0.5)

        # Plot holes
        for interior in poly.interiors:
            x, y = interior.xy
            ax.fill(x, y, fc='white', ec='gray', linewidth=0.5)

    ax.grid(True, alpha=0.3)


def analyze_hole_sharing(poly: Polygon) -> list[tuple[int, int, int, list]]:
    """Find pairs of holes that share vertices."""
    results = []
    for i, hole1 in enumerate(poly.interiors):
        for j, hole2 in enumerate(poly.interiors):
            if i >= j:
                continue

            h1_coords = set(tuple(round(c, 10) for c in pt) for pt in hole1.coords)
            h2_coords = set(tuple(round(c, 10) for c in pt) for pt in hole2.coords)
            shared = h1_coords & h2_coords

            if shared:
                results.append((i, j, len(shared), list(shared)))

    return results


def main():
    # Load test case
    script_dir = Path(__file__).parent
    json_path = script_dir / "fuzzer-spots-12.json"

    if not json_path.exists():
        print(f"Error: {json_path} not found")
        print("Run: python -m tests._fuzzer --generator spots --runs 20 --workers 1")
        return

    print("=" * 70)
    print("OGC Validity Analysis: iOverlay vs Shapely")
    print("=" * 70)

    subject, clip = load_test_case(json_path)

    # Convert inputs to Shapely
    subject_shp = shapes_to_shapely(subject)
    clip_shp = shapes_to_shapely(clip)

    print(f"\nInput shapes:")
    print(f"  Subject: {len(subject)} shape(s), valid={subject_shp.is_valid}")
    print(f"  Clip: {len(clip)} shape(s), valid={clip_shp.is_valid}")

    # Perform XOR with both libraries
    print("\n" + "-" * 70)
    print("Performing XOR operation...")
    print("-" * 70)

    # iOverlay XOR
    ioverlay_result = overlay(subject, clip, OverlayRule.Xor, FillRule.EvenOdd)
    ioverlay_shp = shapes_to_shapely(ioverlay_result)

    # Shapely XOR
    shapely_result = subject_shp.symmetric_difference(clip_shp)

    print(f"\niOverlay result:")
    print(f"  Polygons: {len(ioverlay_shp.geoms)}")
    print(f"  Is valid: {ioverlay_shp.is_valid}")
    print(f"  Area: {ioverlay_shp.area:.6f}")
    if not ioverlay_shp.is_valid:
        print(f"  Validity issue: {explain_validity(ioverlay_shp)}")

    print(f"\nShapely result:")
    print(f"  Polygons: {len(shapely_result.geoms) if isinstance(shapely_result, MultiPolygon) else 1}")
    print(f"  Is valid: {shapely_result.is_valid}")
    print(f"  Area: {shapely_result.area:.6f}")

    print(f"\nArea difference: {abs(ioverlay_shp.area - shapely_result.area):.10f}")

    # Find the invalid polygon and analyze it
    print("\n" + "-" * 70)
    print("Analyzing invalid polygon from iOverlay...")
    print("-" * 70)

    invalid_idx = None
    for i, poly in enumerate(ioverlay_shp.geoms):
        if not poly.is_valid:
            invalid_idx = i
            print(f"\nInvalid polygon index: {i}")
            print(f"  Exterior points: {len(poly.exterior.coords)}")
            print(f"  Number of holes: {len(poly.interiors)}")
            print(f"  Area: {poly.area:.6f}")
            print(f"  Validity issue: {explain_validity(poly)}")

            # Analyze hole sharing
            sharing = analyze_hole_sharing(poly)
            if sharing:
                print(f"\n  Holes sharing vertices:")
                for h1, h2, count, points in sharing:
                    print(f"    Holes {h1} and {h2}: {count} shared point(s)")
                    if count >= 2:
                        print(f"      WARNING: 2+ shared points creates disconnected interior!")
                    for pt in points[:3]:
                        print(f"      - ({pt[0]:.6f}, {pt[1]:.6f})")
            break

    # Generate visualizations
    print("\n" + "-" * 70)
    print("Generating visualizations...")
    print("-" * 70)

    # Figure 1: Overall comparison
    fig1, axes = plt.subplots(1, 3, figsize=(15, 5))

    plot_multipolygon(axes[0], subject_shp, "Subject (input)")
    plot_multipolygon(axes[1], clip_shp, "Clip (input)")
    plot_multipolygon(axes[2], ioverlay_shp, f"iOverlay XOR (valid={ioverlay_shp.is_valid})")

    fig1.suptitle("XOR Operation: Inputs and iOverlay Result", fontsize=14)
    fig1.tight_layout()
    fig1.savefig(script_dir / "comparison_overview.png", dpi=150, bbox_inches='tight')
    print(f"  Saved: {script_dir / 'comparison_overview.png'}")

    # Figure 2: iOverlay vs Shapely comparison
    fig2, axes = plt.subplots(1, 2, figsize=(12, 6))

    plot_multipolygon(axes[0], ioverlay_shp,
                      f"iOverlay XOR\n{len(ioverlay_shp.geoms)} polygons, valid={ioverlay_shp.is_valid}")
    plot_multipolygon(axes[1], shapely_result,
                      f"Shapely XOR\n{len(shapely_result.geoms)} polygons, valid={shapely_result.is_valid}")

    fig2.suptitle("Comparison: iOverlay vs Shapely XOR Results", fontsize=14)
    fig2.tight_layout()
    fig2.savefig(script_dir / "ioverlay_vs_shapely.png", dpi=150, bbox_inches='tight')
    print(f"  Saved: {script_dir / 'ioverlay_vs_shapely.png'}")

    # Figure 3: Zoom in on the invalid polygon
    if invalid_idx is not None:
        invalid_poly = ioverlay_shp.geoms[invalid_idx]

        fig3, axes = plt.subplots(1, 2, figsize=(14, 6))

        # Plot the invalid polygon from iOverlay
        ax = axes[0]
        ax.set_title(f"iOverlay: Invalid Polygon (5 holes)\nRed = polygon with disconnected interior")

        # Plot exterior
        x, y = invalid_poly.exterior.xy
        ax.fill(x, y, alpha=0.3, fc='red', ec='darkred', linewidth=1)

        # Plot holes with different colors
        colors = ['green', 'blue', 'orange', 'purple', 'cyan']
        for i, interior in enumerate(invalid_poly.interiors):
            x, y = interior.xy
            ax.fill(x, y, fc='white', ec=colors[i % len(colors)], linewidth=2,
                   label=f'Hole {i} ({len(interior.coords)} pts)')

        # Mark shared points
        sharing = analyze_hole_sharing(invalid_poly)
        for h1, h2, count, points in sharing:
            if count >= 2:
                for pt in points:
                    ax.plot(pt[0], pt[1], 'ko', markersize=8)
                    ax.annotate(f'shared\n{h1}-{h2}', (pt[0], pt[1]), fontsize=8,
                               xytext=(5, 5), textcoords='offset points')

        ax.legend(loc='upper right', fontsize=8)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)

        # Find and plot equivalent region from Shapely result
        ax2 = axes[1]
        bounds = invalid_poly.bounds
        padding = 2
        ax2.set_xlim(bounds[0] - padding, bounds[2] + padding)
        ax2.set_ylim(bounds[1] - padding, bounds[3] + padding)

        # Find Shapely polygons that intersect this region
        from shapely.geometry import box
        search_box = box(bounds[0] - padding, bounds[1] - padding,
                        bounds[2] + padding, bounds[3] + padding)

        matching_polys = [p for p in shapely_result.geoms if p.intersects(search_box)]
        ax2.set_title(f"Shapely: Same region split into {len(matching_polys)} valid polygons")

        for poly in matching_polys:
            x, y = poly.exterior.xy
            ax2.fill(x, y, alpha=0.3, fc='blue', ec='darkblue', linewidth=1)
            for interior in poly.interiors:
                x, y = interior.xy
                ax2.fill(x, y, fc='white', ec='gray', linewidth=1)

        ax2.set_aspect('equal')
        ax2.grid(True, alpha=0.3)

        fig3.suptitle("Key Difference: iOverlay's Invalid Polygon vs Shapely's Valid Split", fontsize=14)
        fig3.tight_layout()
        fig3.savefig(script_dir / "invalid_polygon_detail.png", dpi=150, bbox_inches='tight')
        print(f"  Saved: {script_dir / 'invalid_polygon_detail.png'}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"""
Key findings:
1. Same inputs, same operation (XOR with EvenOdd)
2. iOverlay produces 35 polygons, 1 INVALID
3. Shapely produces 38 polygons, ALL VALID
4. Areas are identical: {ioverlay_shp.area:.6f}

The invalid polygon has 5 holes where:
- Holes 0 and 1 share 2 points
- Holes 0 and 3 share 2 points
- Holes 2 and 3 share 2 points

When holes share 2+ points, they create a "corridor" that disconnects
the polygon's interior, violating OGC's requirement that polygon
interiors must be connected.

Shapely avoids this by splitting such polygons into multiple valid
polygons at the pinch points.
""")

    plt.show()


if __name__ == "__main__":
    main()
