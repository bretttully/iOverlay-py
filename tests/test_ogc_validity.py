"""Tests for OGC validity of overlay results.

These tests document known issues where iOverlay produces geometries that
violate OGC Simple Feature Specification validity rules.

See docs/ogc-validity-differences.md for detailed analysis.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
import pytest
import shapely
from shapely.validation import explain_validity

from i_overlay import FillRule, OverlayRule, overlay

from .shapely_utils import Shapes, geometry_to_shapes


def shapes_to_multipolygon_unchecked(shapes: Shapes) -> shapely.MultiPolygon:
    """Convert i_overlay shapes to Shapely MultiPolygon without validity filtering.

    Unlike the standard shapes_to_multipolygon, this does NOT filter out invalid
    polygons, allowing us to detect OGC validity issues.
    """
    polygons = []
    for shape in shapes:
        if not shape:
            continue
        exterior = shape[0]
        holes = shape[1:] if len(shape) > 1 else None
        try:
            polygon = shapely.Polygon(exterior, holes)
            if not polygon.is_empty:
                polygons.append(polygon)
        except Exception:
            pass
    return shapely.MultiPolygon(polygons) if polygons else shapely.MultiPolygon()


@dataclass
class OGCValidityTestCase:
    """Test case for OGC validity issues."""

    id: str
    description: str
    exterior: shapely.Polygon
    interior: shapely.Polygon
    expected_area: float
    xfail: bool = False
    xfail_reason: str = ""

    def pytest_param(self) -> Any:
        """Return a pytest.param with appropriate markers."""
        marks = []
        if self.xfail:
            marks.append(pytest.mark.xfail(reason=self.xfail_reason))
        return pytest.param(self, id=self.id, marks=marks)


TWO_HOLES_CASE = OGCValidityTestCase(
    id="two_holes_sharing_vertices",
    description="""
    Two L-shaped holes share vertices at (2,2) and (3,3):
        0   1   2   3   4   5
      5 ┌───────────────────┐
        │                   │
      4 │   ┌───────┐       │
        │   │ ░   ░ │       │
      3 │   │   ┌───●───┐   │
        │   │ ░ │   │ ░ │   │   ░ = holes
      2 │   └───●───┘   │   │
        │       │ ░   ░ │   │
      1 │       └───────┘   │
        │                   │
      0 └───────────────────┘
    """,
    exterior=shapely.box(0, 0, 5, 5),
    interior=shapely.union_all(
        [
            shapely.box(1, 2, 2, 4),
            shapely.box(2, 3, 3, 4),
            shapely.box(2, 1, 4, 2),
            shapely.box(3, 2, 4, 3),
        ]
    ),
    expected_area=19.0,  # 25 (box) - 3 (top_l) - 3 (bottom_l)
    xfail=True,
    xfail_reason="iOverlay produces invalid polygons when holes share 2+ vertices",
)

SINGLE_HOLE_CASE = OGCValidityTestCase(
    id="single_hole_sharing_vertices",
    description="""
    Single combined hole shares vertices at (2,2) and (2,3):
        0   1   2   3   4
      4         ┌───────┐
                │       │
      3     ┌───●───┐   │
            │   │ ░ │   │   Single L-shaped hole shares vertices ● at (2,2) and (2,3)
      2 ┌───●───┘   │   │
        │   │ ░   ░ │   │   ░ = hole
      1 │   └───────┘   │
        │               │
      0 └───────────────┘
    """,
    exterior=shapely.box(0, 0, 4, 4),
    interior=shapely.union_all(
        [
            shapely.box(0, 2, 1, 4),
            shapely.box(1, 3, 2, 4),
            shapely.box(1, 1, 3, 2),
            shapely.box(2, 2, 3, 3),
        ]
    ),
    expected_area=10.0,  # 16 (box) - 6 (combined holes)
    xfail=False,
)


def create_checkerboard(level: int):
    base_sz = 7
    sz = base_sz ** (level + 1)
    exterior = shapely.box(0, 0, sz, sz)

    def interiors(ilevel: int):
        szi = base_sz**ilevel
        return [
            *(shapely.box(i * szi, i * szi, (i + 1) * szi, (i + 1) * szi) for i in range(1, 6)),
            *(shapely.box(i * szi, (i + 2) * szi, (i + 1) * szi, (i + 3) * szi) for i in range(1, 4)),
            *(shapely.box(i * szi, (i + 4) * szi, (i + 1) * szi, (i + 5) * szi) for i in range(1, 2)),
            *(shapely.box((i + 2) * szi, i * szi, (i + 3) * szi, (i + 1) * szi) for i in range(1, 4)),
            *(shapely.box((i + 4) * szi, i * szi, (i + 5) * szi, (i + 1) * szi) for i in range(1, 2)),
        ]

    holes = []
    for ilevel in range(level + 1):
        holes.extend(interiors(ilevel))
        if ilevel < level:
            offset = base_sz ** (ilevel + 1)
            holes = [shapely.transform(h, lambda p, o=offset: p + np.array([2 * o, 3 * o])) for h in holes]

    interior = shapely.unary_union(holes)
    expected_area = exterior.area - interior.area
    return {"exterior": exterior, "interior": interior, "expected_area": expected_area}


CHECKERBOARD_LVL0_CASE = OGCValidityTestCase(
    id="checkerboard_level_0",
    description="""
        0   1   2   3   4   5   6   7
      7 ┌───────────────────────────┐
        │                           │
      6 │   ┌───┐   ┌───┐   ┌───┐   │
        │   │ ░ │   │ ░ │   │ ░ │   │
      5 │   └───●───●───●───●───┘   │
        │       │ ░ │   │ ░ │       │
      4 │   ┌───●───●───●───●───┐   │
        │   │ ░ │   │ ░ │   │ ░ │   │   ░ = holes
      3 │   └───●───●───●───●───┘   │
        │       │ ░ │   │ ░ │       │
      2 │   ┌───●───●───●───●───┐   │
        │   │ ░ │   │ ░ │   │ ░ │   │
      1 │   └───┘   └───┘   └───┘   │
        │                           │
      0 └───────────────────────────┘
    """,
    **create_checkerboard(level=0),
    xfail=True,
    xfail_reason="iOverlay produces invalid polygons when holes share 2+ vertices",
)


CHECKERBOARD_LVL1_CASE = OGCValidityTestCase(
    id="checkerboard_level_1",
    description="""
    A single level nested version of the checkerboard pattern where holes share vertices and the sub-checkerboard
    is itself the level 0 checkerboard and located at (14,21):

        0   1   2   3   4   5   6   7
      7 ┌───────────────────────────┐
        │                           │
      6 │   ┌───┐   ┌───┐   ┌───┐   │
        │   │ ░ │   │ ░ │   │ ░ │   │
      5 │   └───●───●───●───●───┘   │
        │       │ ░ │   │ ░ │       │
      4 │   ┌───●───●───●───●───┐   │
        │   │ ░ │   │ ░ │   │ ░ │   │   ░ = holes
      3 │   └───●───●───●───●───┘   │
        │       │ ░ │   │ ░ │       │
      2 │   ┌───●───●───●───●───┐   │
        │   │ ░ │   │ ░ │   │ ░ │   │
      1 │   └───┘   └───┘   └───┘   │
        │                           │
      0 └───────────────────────────┘
    """,
    **create_checkerboard(level=1),
    xfail=True,
    xfail_reason="iOverlay produces invalid polygons when holes share 2+ vertices",
)


CHECKERBOARD_LVL2_CASE = OGCValidityTestCase(
    id="checkerboard_level_2",
    description="""
    A two-level nested version of the checkerboard pattern where holes share vertices and the sub-checkerboards
    are themselves the level 1 checkerboard located at (98,147):
        0   1   2   3   4   5   6   7
      7 ┌───────────────────────────┐
        │                           │
      6 │   ┌───┐   ┌───┐   ┌───┐   │
        │   │ ░ │   │ ░ │   │ ░ │   │
      5 │   └───●───●───●───●───┘   │
        │       │ ░ │   │ ░ │       │
      4 │   ┌───●───●───●───●───┐   │
        │   │ ░ │   │ ░ │   │ ░ │   │   ░ = holes
      3 │   └───●───●───●───●───┘   │
        │       │ ░ │   │ ░ │       │
      2 │   ┌───●───●───●───●───┐   │
        │   │ ░ │   │ ░ │   │ ░ │   │
      1 │   └───┘   └───┘   └───┘   │
        │                           │
      0 └───────────────────────────┘
    """,
    **create_checkerboard(level=2),
    xfail=True,
    xfail_reason="iOverlay produces invalid polygons when holes share 2+ vertices",
)


class TestOGCValidity:
    """Tests documenting known OGC validity issues in iOverlay.

    OGC Simple Feature Specification (ISO 19125-1) states:
    "The interior of every Surface is a connected point set."

    When holes share two or more vertices, they can disconnect the interior,
    creating an invalid polygon. Shapely handles this by splitting into
    multiple valid polygons; iOverlay currently does not.
    """

    @pytest.mark.parametrize(
        "case",
        [
            TWO_HOLES_CASE.pytest_param(),
            SINGLE_HOLE_CASE.pytest_param(),
            CHECKERBOARD_LVL0_CASE.pytest_param(),
            CHECKERBOARD_LVL1_CASE.pytest_param(),
            CHECKERBOARD_LVL2_CASE.pytest_param(),
        ],
    )
    def test_ioverlay_vs_shapely_validity(self, case: OGCValidityTestCase) -> None:
        """Compare iOverlay and Shapely results for difference operations.

        Both should produce same total area and valid geometry.
        """
        exterior_shapes = geometry_to_shapes(case.exterior)
        interior_shapes = geometry_to_shapes(case.interior)

        # iOverlay result
        ioverlay_result = overlay(exterior_shapes, interior_shapes, OverlayRule.Difference, FillRule.EvenOdd)
        ioverlay_mp = shapes_to_multipolygon_unchecked(ioverlay_result)

        # Shapely result
        shapely_result = case.exterior.difference(case.interior)

        # Both should have correct area
        assert ioverlay_mp.area == pytest.approx(case.expected_area)
        assert shapely_result.area == pytest.approx(case.expected_area)

        # Shapely should produce valid MultiPolygon split into 2 polygons
        assert isinstance(shapely_result, shapely.MultiPolygon)
        assert len(shapely_result.geoms) == 2
        assert shapely_result.is_valid, f"Shapely produced invalid geometry: {explain_validity(shapely_result)}"

        # iOverlay should also be valid (this is what fails)
        assert ioverlay_mp.is_valid, f"iOverlay produced invalid geometry: {explain_validity(ioverlay_mp)}"

        # Results should be geometrically equal
        assert ioverlay_mp.equals(shapely_result), f"{ioverlay_mp.wkt=} != {shapely_result.wkt=}"
