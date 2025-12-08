"""Tests for OGC validity of overlay results.

These tests document known issues where iOverlay produces geometries that
violate OGC Simple Feature Specification validity rules.

See docs/ogc-validity-differences.md for detailed analysis.
"""

import pytest
import shapely
from shapely.validation import explain_validity

from i_overlay import FillRule, OverlayRule, overlay

from .shapely_utils import Shapes, geometry_to_shapes

# Expected area: 25 (box) - 3 (top_l) - 3 (bottom_l) = 19
EXPECTED_AREA = 19.0


def shapes_to_multipolygon_unchecked(shapes: Shapes) -> shapely.MultiPolygon:
    """Convert i_overlay shapes to Shapely shapely.MultiPolygon without validity filtering.

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


@pytest.fixture
def box_shapely() -> shapely.Polygon:
    """5x5 box polygon."""
    return shapely.box(0, 0, 5, 5)


@pytest.fixture
def top_l_shapely() -> shapely.Polygon:
    """Top-left L-shaped hole (area=3).

    Covers cells: (1,2)-(2,3), (1,3)-(2,4), (2,3)-(3,4)
    """
    return shapely.union_all(
        [
            shapely.box(1, 3, 2, 4),  # top-left cell
            shapely.box(2, 3, 3, 4),  # top-right cell
            shapely.box(1, 2, 2, 3),  # bottom cell
        ]
    )


@pytest.fixture
def bottom_l_shapely() -> shapely.Polygon:
    """Bottom-right L-shaped hole (area=3).

    Covers cells: (3,2)-(4,3), (2,1)-(3,2), (3,1)-(4,2)
    """
    return shapely.union_all(
        [
            shapely.box(3, 2, 4, 3),  # top cell
            shapely.box(2, 1, 3, 2),  # bottom-left cell
            shapely.box(3, 1, 4, 2),  # bottom-right cell
        ]
    )


@pytest.fixture
def box_shapes(box_shapely: shapely.Polygon) -> Shapes:
    """5x5 box as i_overlay Shapes."""
    return geometry_to_shapes(box_shapely)


@pytest.fixture
def top_l_shapes(top_l_shapely: shapely.Polygon) -> Shapes:
    """Top-left L-shaped hole as i_overlay Shapes."""
    return geometry_to_shapes(top_l_shapely)


@pytest.fixture
def bottom_l_shapes(bottom_l_shapely: shapely.Polygon) -> Shapes:
    """Bottom-right L-shaped hole as i_overlay Shapes."""
    return geometry_to_shapes(bottom_l_shapely)


class TestOGCValidityKnownIssues:
    """Tests documenting known OGC validity issues in iOverlay.

    These tests are marked as xfail because they document bugs in the upstream
    iOverlay library. When iOverlay fixes these issues, the tests should pass.

    Diagram of the test geometry:
        0   1   2   3   4   5
      5 ┌───────────────────┐
        │                   │
      4 │   ┌───────┐       │
        │   │ ░   ░ │       │   Two L-shaped holes share vertices ● at (2,2) and (3,3)
      3 │   │   ┌───●───┐   │
        │   │ ░ │   │ ░ │   │   ░ = holes
      2 │   └───●───┘   │   │
        │       │ ░   ░ │   │   The shared diagonal edge disconnects the interior
      1 │       └───────┘   │
        │                   │
      0 └───────────────────┘

    OGC Simple Feature Specification (ISO 19125-1) states:
    "The interior of every Surface is a connected point set."
    """

    @pytest.mark.xfail(reason="iOverlay produces invalid polygons when holes share 2+ vertices")
    def test_holes_sharing_two_vertices_creates_invalid_polygon(
        self, box_shapes: Shapes, top_l_shapes: Shapes, bottom_l_shapes: Shapes
    ) -> None:
        """Test that holes sharing two vertices creates disconnected interior."""
        # Subtract both L shapes from the box using iOverlay
        step1 = overlay(box_shapes, top_l_shapes, OverlayRule.Difference, FillRule.EvenOdd)
        result = overlay(step1, bottom_l_shapes, OverlayRule.Difference, FillRule.EvenOdd)

        # Convert to Shapely (without filtering invalid polygons)
        result_mp = shapes_to_multipolygon_unchecked(result)

        # Verify area is correct before checking validity
        assert result_mp.area == pytest.approx(EXPECTED_AREA)

        # The result should be valid (OGC requirement)
        assert result_mp.is_valid, f"iOverlay produced invalid geometry: {explain_validity(result_mp)}"

    def test_shapely_handles_touching_holes_correctly(
        self, box_shapely: shapely.Polygon, top_l_shapely: shapely.Polygon, bottom_l_shapely: shapely.Polygon
    ) -> None:
        """Verify that Shapely produces valid output for the same operation.

        This proves that valid output is achievable - Shapely splits the
        polygon at the pinch points to produce multiple valid polygons.
        """
        result = box_shapely.difference(top_l_shapely).difference(bottom_l_shapely)

        # Verify area is correct
        assert result.area == pytest.approx(EXPECTED_AREA)

        # Shapely should produce a valid shapely.MultiPolygon
        assert isinstance(result, shapely.MultiPolygon)

        # Shapely splits into 2 polygons to maintain validity
        assert len(result.geoms) == 2

        assert result.is_valid, f"Shapely produced invalid geometry: {explain_validity(result)}"

    @pytest.mark.xfail(reason="iOverlay produces invalid polygons when holes share 2+ vertices")
    def test_ioverlay_vs_shapely_validity(
        self,
        box_shapely: shapely.Polygon,
        top_l_shapely: shapely.Polygon,
        bottom_l_shapely: shapely.Polygon,
        box_shapes: Shapes,
        top_l_shapes: Shapes,
        bottom_l_shapes: Shapes,
    ) -> None:
        """Compare iOverlay and Shapely results for the same operation.

        Both should produce same total area and valid geometry.
        """
        # iOverlay result
        step1 = overlay(box_shapes, top_l_shapes, OverlayRule.Difference, FillRule.EvenOdd)
        ioverlay_result = overlay(step1, bottom_l_shapes, OverlayRule.Difference, FillRule.EvenOdd)
        ioverlay_mp = shapes_to_multipolygon_unchecked(ioverlay_result)

        # Shapely result
        shapely_result = box_shapely.difference(top_l_shapely).difference(bottom_l_shapely)

        # Both should have correct area
        assert ioverlay_mp.area == pytest.approx(EXPECTED_AREA)
        assert shapely_result.area == pytest.approx(EXPECTED_AREA)

        # Both should be valid
        assert shapely_result.is_valid, f"Shapely produced invalid geometry: {explain_validity(shapely_result)}"
        assert ioverlay_mp.is_valid, f"iOverlay produced invalid geometry: {explain_validity(ioverlay_mp)}"
