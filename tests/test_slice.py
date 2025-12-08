"""Tests for slice_by function."""

import shapely

from i_overlay import (
    FillRule,
    OverlayOptions,
    Solver,
    slice_by,
)

from .shapely_utils import box, shapes_to_multipolygon


class TestSliceBasic:
    """Basic tests for slice_by function."""

    def test_slice_square_horizontal(self) -> None:
        """Test slicing a square horizontally."""
        shape = box(0.0, 0.0, 2.0, 2.0)
        # Horizontal line through the middle
        polylines = [[(0.0, 1.0), (2.0, 1.0)]]

        result = slice_by(shape, polylines, FillRule.EvenOdd)
        result_geom = shapes_to_multipolygon(result)

        # Should produce two rectangles
        assert len(result) == 2
        # Total area should be preserved
        assert abs(result_geom.area - 4.0) < 1e-6
        # Should produce bottom and top rectangles
        expected = shapely.MultiPolygon(
            [
                shapely.box(0.0, 0.0, 2.0, 1.0),
                shapely.box(0.0, 1.0, 2.0, 2.0),
            ]
        )
        assert result_geom.equals(expected)

    def test_slice_square_vertical(self) -> None:
        """Test slicing a square vertically."""
        shape = box(0.0, 0.0, 2.0, 2.0)
        # Vertical line through the middle
        polylines = [[(1.0, 0.0), (1.0, 2.0)]]

        result = slice_by(shape, polylines, FillRule.EvenOdd)
        result_geom = shapes_to_multipolygon(result)

        # Should produce two rectangles
        assert len(result) == 2
        assert abs(result_geom.area - 4.0) < 1e-6
        # Should produce left and right rectangles
        expected = shapely.MultiPolygon(
            [
                shapely.box(0.0, 0.0, 1.0, 2.0),
                shapely.box(1.0, 0.0, 2.0, 2.0),
            ]
        )
        assert result_geom.equals(expected)

    def test_slice_square_diagonal(self) -> None:
        """Test slicing a square diagonally."""
        shape = box(0.0, 0.0, 2.0, 2.0)
        # Diagonal line
        polylines = [[(0.0, 0.0), (2.0, 2.0)]]

        result = slice_by(shape, polylines, FillRule.EvenOdd)
        result_geom = shapes_to_multipolygon(result)

        # Should produce two triangles
        assert len(result) == 2
        assert abs(result_geom.area - 4.0) < 1e-6
        # Should produce two triangles - bottom-right and top-left
        expected = shapely.MultiPolygon(
            [
                shapely.Polygon([(0.0, 0.0), (2.0, 0.0), (2.0, 2.0)]),
                shapely.Polygon([(0.0, 0.0), (2.0, 2.0), (0.0, 2.0)]),
            ]
        )
        assert result_geom.equals(expected)


class TestSliceMultipleLines:
    """Tests for slicing with multiple polylines."""

    def test_slice_grid(self) -> None:
        """Test slicing a square into a 2x2 grid."""
        shape = box(0.0, 0.0, 2.0, 2.0)
        # Cross pattern
        polylines = [
            [(0.0, 1.0), (2.0, 1.0)],  # Horizontal
            [(1.0, 0.0), (1.0, 2.0)],  # Vertical
        ]

        result = slice_by(shape, polylines, FillRule.EvenOdd)
        result_geom = shapes_to_multipolygon(result)

        # Should produce 4 squares
        assert len(result) == 4
        assert abs(result_geom.area - 4.0) < 1e-6
        # Should produce four unit squares
        expected = shapely.MultiPolygon(
            [
                shapely.box(0.0, 0.0, 1.0, 1.0),
                shapely.box(1.0, 0.0, 2.0, 1.0),
                shapely.box(0.0, 1.0, 1.0, 2.0),
                shapely.box(1.0, 1.0, 2.0, 2.0),
            ]
        )
        assert result_geom.equals(expected)


class TestSlicePartial:
    """Tests for partial slicing (line doesn't fully cross shape)."""

    def test_slice_partial_line(self) -> None:
        """Test slicing with a line that partially enters the shape."""
        shape = box(0.0, 0.0, 2.0, 2.0)
        # Line starts outside, enters shape, doesn't exit
        polylines = [[(-1.0, 1.0), (1.0, 1.0)]]

        result = slice_by(shape, polylines, FillRule.EvenOdd)
        result_geom = shapes_to_multipolygon(result)

        # Area should be preserved
        assert abs(result_geom.area - 4.0) < 1e-6

    def test_slice_line_outside(self) -> None:
        """Test slicing with a line completely outside the shape."""
        shape = box(0.0, 0.0, 2.0, 2.0)
        # Line completely outside
        polylines = [[(5.0, 0.0), (5.0, 2.0)]]

        result = slice_by(shape, polylines, FillRule.EvenOdd)
        result_geom = shapes_to_multipolygon(result)

        # Shape should be unchanged
        expected = shapely.box(0.0, 0.0, 2.0, 2.0)
        assert result_geom.equals(expected)


class TestSliceWithOptions:
    """Tests for slice_by with custom options."""

    def test_with_options(self) -> None:
        """Test slice_by with custom options."""
        shape = box(0.0, 0.0, 2.0, 2.0)
        polylines = [[(0.0, 1.0), (2.0, 1.0)]]

        options = OverlayOptions(preserve_input_collinear=True)
        result = slice_by(shape, polylines, FillRule.EvenOdd, options=options)
        result_geom = shapes_to_multipolygon(result)

        assert len(result) == 2
        assert abs(result_geom.area - 4.0) < 1e-6

    def test_with_solver(self) -> None:
        """Test slice_by with custom solver."""
        shape = box(0.0, 0.0, 2.0, 2.0)
        polylines = [[(0.0, 1.0), (2.0, 1.0)]]

        result = slice_by(shape, polylines, FillRule.EvenOdd, solver=Solver.AUTO)
        result_geom = shapes_to_multipolygon(result)

        assert len(result) == 2
        assert abs(result_geom.area - 4.0) < 1e-6


class TestSliceEdgeCases:
    """Tests for slice_by edge cases."""

    def test_empty_shapes(self) -> None:
        """Test slicing empty shapes."""
        shapes: list[list[list[tuple[float, float]]]] = []
        polylines = [[(0.0, 1.0), (2.0, 1.0)]]

        result = slice_by(shapes, polylines, FillRule.EvenOdd)
        result_geom = shapes_to_multipolygon(result)

        assert result_geom.is_empty

    def test_empty_polylines(self) -> None:
        """Test slicing with empty polylines."""
        shape = box(0.0, 0.0, 2.0, 2.0)
        polylines: list[list[tuple[float, float]]] = []

        result = slice_by(shape, polylines, FillRule.EvenOdd)
        result_geom = shapes_to_multipolygon(result)

        # Shape should be unchanged
        expected = shapely.box(0.0, 0.0, 2.0, 2.0)
        assert result_geom.equals(expected)

    def test_slice_along_edge(self) -> None:
        """Test slicing along an edge of the shape."""
        shape = box(0.0, 0.0, 2.0, 2.0)
        # Line along the bottom edge
        polylines = [[(0.0, 0.0), (2.0, 0.0)]]

        result = slice_by(shape, polylines, FillRule.EvenOdd)
        result_geom = shapes_to_multipolygon(result)

        # Shape should be unchanged (line is on boundary)
        assert abs(result_geom.area - 4.0) < 1e-6
