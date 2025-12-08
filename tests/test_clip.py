"""Tests for clip_by function."""

import shapely

from i_overlay import (
    ClipRule,
    FillRule,
    Solver,
    clip_by,
)

from .shapely_utils import box, geometry_to_shapes


class TestClipBasic:
    """Basic tests for clip_by function."""

    def test_clip_line_through_square(self) -> None:
        """Test clipping a line that passes through a square."""
        # A square
        shapes = box(0.0, 0.0, 2.0, 2.0)
        # A horizontal line passing through the square
        polylines = [[(-1.0, 1.0), (3.0, 1.0)]]

        result = clip_by(polylines, shapes, FillRule.EvenOdd, ClipRule())

        # Should produce one segment inside the square
        assert len(result) == 1
        # The clipped segment should be from (0, 1) to (2, 1)
        expected_line = shapely.LineString([(0.0, 1.0), (2.0, 1.0)])
        result_line = shapely.LineString(result[0])
        assert result_line.equals(expected_line)

    def test_clip_line_inside_square(self) -> None:
        """Test clipping a line entirely inside a square."""
        shapes = box(0.0, 0.0, 2.0, 2.0)
        # A line entirely inside
        polylines = [[(0.5, 1.0), (1.5, 1.0)]]

        result = clip_by(polylines, shapes, FillRule.EvenOdd, ClipRule())

        # Line should be unchanged
        assert len(result) == 1
        expected_line = shapely.LineString([(0.5, 1.0), (1.5, 1.0)])
        result_line = shapely.LineString(result[0])
        assert result_line.equals(expected_line)

    def test_clip_line_outside_square(self) -> None:
        """Test clipping a line entirely outside a square."""
        shapes = box(0.0, 0.0, 2.0, 2.0)
        # A line entirely outside
        polylines = [[(5.0, 0.0), (5.0, 2.0)]]

        result = clip_by(polylines, shapes, FillRule.EvenOdd, ClipRule())

        # No segments should remain
        assert len(result) == 0


class TestClipInvert:
    """Tests for clip_by with invert option."""

    def test_clip_invert(self) -> None:
        """Test clipping with invert=True keeps outside portion."""
        shapes = box(0.0, 0.0, 2.0, 2.0)
        # A horizontal line passing through the square
        polylines = [[(-1.0, 1.0), (3.0, 1.0)]]

        result = clip_by(
            polylines,
            shapes,
            FillRule.EvenOdd,
            ClipRule(invert=True),
        )

        # Should produce two segments outside the square
        assert len(result) == 2
        # Total length should be 2 (1 unit on each side)
        total_length = sum(shapely.LineString(r).length for r in result)
        assert abs(total_length - 2.0) < 1e-6


class TestClipBoundary:
    """Tests for clip_by with boundary options."""

    def test_clip_on_boundary_included(self) -> None:
        """Test clipping a line on the boundary with boundary_included=True."""
        shapes = box(0.0, 0.0, 2.0, 2.0)
        # A line along the left edge
        polylines = [[(0.0, 0.0), (0.0, 2.0)]]

        result = clip_by(
            polylines,
            shapes,
            FillRule.EvenOdd,
            ClipRule(boundary_included=True),
        )

        # Boundary line should be included
        assert len(result) == 1

    def test_clip_on_boundary_excluded(self) -> None:
        """Test clipping a line on the boundary with boundary_included=False."""
        shapes = box(0.0, 0.0, 2.0, 2.0)
        # A line along the left edge
        polylines = [[(0.0, 0.0), (0.0, 2.0)]]

        result = clip_by(
            polylines,
            shapes,
            FillRule.EvenOdd,
            ClipRule(boundary_included=False),
        )

        # Boundary line should be excluded
        assert len(result) == 0


class TestClipMultipleLines:
    """Tests for clipping multiple polylines."""

    def test_clip_multiple_lines(self) -> None:
        """Test clipping multiple polylines at once."""
        shapes = box(0.0, 0.0, 2.0, 2.0)
        # Multiple lines
        polylines = [
            [(-1.0, 0.5), (3.0, 0.5)],  # Through bottom half
            [(-1.0, 1.5), (3.0, 1.5)],  # Through top half
        ]

        result = clip_by(polylines, shapes, FillRule.EvenOdd, ClipRule())

        # Should produce two segments
        assert len(result) == 2
        # Each segment should have length 2
        for segment in result:
            length = shapely.LineString(segment).length
            assert abs(length - 2.0) < 1e-6


class TestClipComplexPath:
    """Tests for clipping complex polylines."""

    def test_clip_polyline_multiple_segments(self) -> None:
        """Test clipping a polyline with multiple segments."""
        shapes = box(0.0, 0.0, 2.0, 2.0)
        # A polyline that enters and exits the square multiple times
        polylines = [[(-1.0, 1.0), (1.0, 1.0), (1.0, 3.0)]]

        result = clip_by(polylines, shapes, FillRule.EvenOdd, ClipRule())

        # Should produce segments for portions inside
        assert len(result) >= 1
        # Total area covered should be inside the square
        for segment in result:
            line = shapely.LineString(segment)
            square = shapely.box(0.0, 0.0, 2.0, 2.0)
            assert square.contains(line) or square.touches(line)


class TestClipWithSolver:
    """Tests for clip_by with custom solver."""

    def test_with_solver(self) -> None:
        """Test clip_by with custom solver."""
        shapes = box(0.0, 0.0, 2.0, 2.0)
        polylines = [[(-1.0, 1.0), (3.0, 1.0)]]

        result = clip_by(
            polylines,
            shapes,
            FillRule.EvenOdd,
            ClipRule(),
            solver=Solver.AUTO,
        )

        assert len(result) == 1
        expected_line = shapely.LineString([(0.0, 1.0), (2.0, 1.0)])
        result_line = shapely.LineString(result[0])
        assert result_line.equals(expected_line)


class TestClipEdgeCases:
    """Tests for clip_by edge cases."""

    def test_empty_polylines(self) -> None:
        """Test clipping empty polylines."""
        shapes = box(0.0, 0.0, 2.0, 2.0)
        polylines: list[list[tuple[float, float]]] = []

        result = clip_by(polylines, shapes, FillRule.EvenOdd, ClipRule())

        assert len(result) == 0

    def test_empty_shapes(self) -> None:
        """Test clipping against empty shapes."""
        shapes: list[list[list[tuple[float, float]]]] = []
        polylines = [[(-1.0, 1.0), (3.0, 1.0)]]

        result = clip_by(polylines, shapes, FillRule.EvenOdd, ClipRule())

        # With no shapes, nothing is inside (depends on invert setting)
        # Without invert, should return empty
        assert len(result) == 0

    def test_clip_with_hole(self) -> None:
        """Test clipping against a shape with a hole."""
        # Outer square with inner hole
        outer = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)]
        hole = [(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)]
        shapes = geometry_to_shapes(shapely.Polygon(outer, [hole]))

        # A line passing through the shape and hole
        polylines = [[(-1.0, 2.0), (5.0, 2.0)]]

        result = clip_by(polylines, shapes, FillRule.EvenOdd, ClipRule())

        # Should produce two segments (one on each side of the hole)
        assert len(result) == 2
        # Each segment should be 1 unit long (from 0-1 and 3-4)
        lengths = sorted(shapely.LineString(r).length for r in result)
        assert abs(lengths[0] - 1.0) < 1e-6
        assert abs(lengths[1] - 1.0) < 1e-6
