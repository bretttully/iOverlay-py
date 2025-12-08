"""Tests for simplify_shape function."""

import shapely

from i_overlay import (
    FillRule,
    OverlayOptions,
    Solver,
    simplify_shape,
)

from .shapely_utils import box, geometry_to_shapes, shapes_to_multipolygon


class TestSimplifyBasic:
    """Basic tests for simplify_shape function."""

    def test_simplify_simple_shape(self) -> None:
        """Test simplifying a simple shape (no change expected)."""
        shape = box(0.0, 0.0, 2.0, 2.0)

        result = simplify_shape(shape, FillRule.EvenOdd)
        result_geom = shapes_to_multipolygon(result)

        expected = shapely.box(0.0, 0.0, 2.0, 2.0)
        assert result_geom.equals(expected)

    def test_simplify_collinear_points(self) -> None:
        """Test simplifying a shape with collinear points."""
        # Rectangle with extra collinear point on edge
        shape = [[[(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]]]

        result = simplify_shape(shape, FillRule.EvenOdd)
        result_geom = shapes_to_multipolygon(result)

        # Should produce valid rectangle shape
        expected = shapely.box(0.0, 0.0, 2.0, 2.0)
        assert result_geom.equals(expected)


class TestSimplifySelfIntersection:
    """Tests for simplifying self-intersecting shapes."""

    def test_simplify_figure_eight(self) -> None:
        """Test simplifying a figure-8 (self-intersecting) shape."""
        # A figure-8 shape that crosses itself at (1, 1)
        figure_eight = [[[(0.0, 0.0), (2.0, 2.0), (2.0, 0.0), (0.0, 2.0)]]]

        result = simplify_shape(figure_eight, FillRule.EvenOdd)
        result_geom = shapes_to_multipolygon(result)

        # With EvenOdd rule, should produce two triangles
        # Total area should be 2 (two triangles of area 1 each)
        assert abs(result_geom.area - 2.0) < 1e-6
        assert result_geom.is_valid
        # Should produce two triangles meeting at (1, 1)
        expected = shapely.MultiPolygon(
            [
                shapely.Polygon([(0.0, 0.0), (1.0, 1.0), (0.0, 2.0)]),
                shapely.Polygon([(2.0, 0.0), (1.0, 1.0), (2.0, 2.0)]),
            ]
        )
        assert result_geom.equals(expected)

    def test_simplify_figure_eight_nonzero(self) -> None:
        """Test simplifying figure-8 with NonZero fill rule."""
        # A figure-8 shape that crosses itself at (1, 1)
        figure_eight = [[[(0.0, 0.0), (2.0, 2.0), (2.0, 0.0), (0.0, 2.0)]]]

        result = simplify_shape(figure_eight, FillRule.NonZero)
        result_geom = shapes_to_multipolygon(result)

        # NonZero fills any area with non-zero winding - same result as EvenOdd here
        assert result_geom.is_valid
        assert abs(result_geom.area - 2.0) < 1e-6
        # Should produce two triangles meeting at (1, 1)
        expected = shapely.MultiPolygon(
            [
                shapely.Polygon([(0.0, 0.0), (1.0, 1.0), (0.0, 2.0)]),
                shapely.Polygon([(2.0, 0.0), (1.0, 1.0), (2.0, 2.0)]),
            ]
        )
        assert result_geom.equals(expected)


class TestSimplifyOverlapping:
    """Tests for simplifying overlapping shapes."""

    def test_simplify_overlapping_squares_nonzero(self) -> None:
        """Test simplifying two overlapping squares with NonZero fill rule."""
        # Two overlapping squares as separate shapes in the subject
        shapes = [
            geometry_to_shapes(shapely.box(0.0, 0.0, 2.0, 2.0))[0],
            geometry_to_shapes(shapely.box(1.0, 1.0, 3.0, 3.0))[0],
        ]

        # NonZero fills any area with non-zero winding number
        result = simplify_shape(shapes, FillRule.NonZero)
        result_geom = shapes_to_multipolygon(result)

        # Should produce union of the two squares
        expected = shapely.box(0.0, 0.0, 2.0, 2.0).union(shapely.box(1.0, 1.0, 3.0, 3.0))
        assert result_geom.equals(expected)

    def test_simplify_overlapping_squares_evenodd(self) -> None:
        """Test simplifying two overlapping squares with EvenOdd fill rule."""
        # Two overlapping squares as separate shapes in the subject
        shapes = [
            geometry_to_shapes(shapely.box(0.0, 0.0, 2.0, 2.0))[0],
            geometry_to_shapes(shapely.box(1.0, 1.0, 3.0, 3.0))[0],
        ]

        # EvenOdd cancels overlapping areas (XOR-like behavior)
        result = simplify_shape(shapes, FillRule.EvenOdd)
        result_geom = shapes_to_multipolygon(result)

        # With EvenOdd, overlapping area is cancelled out (like XOR)
        expected = shapely.box(0.0, 0.0, 2.0, 2.0).symmetric_difference(shapely.box(1.0, 1.0, 3.0, 3.0))
        assert result_geom.equals(expected)


class TestSimplifyWithOptions:
    """Tests for simplify_shape with custom options."""

    def test_with_options(self) -> None:
        """Test simplify_shape with custom options."""
        shape = box(0.0, 0.0, 2.0, 2.0)

        options = OverlayOptions(preserve_input_collinear=True)
        result = simplify_shape(shape, FillRule.EvenOdd, options=options)
        result_geom = shapes_to_multipolygon(result)

        expected = shapely.box(0.0, 0.0, 2.0, 2.0)
        assert result_geom.equals(expected)

    def test_with_solver(self) -> None:
        """Test simplify_shape with custom solver."""
        shape = box(0.0, 0.0, 2.0, 2.0)

        result = simplify_shape(shape, FillRule.EvenOdd, solver=Solver.AUTO)
        result_geom = shapes_to_multipolygon(result)

        expected = shapely.box(0.0, 0.0, 2.0, 2.0)
        assert result_geom.equals(expected)


class TestSimplifyEdgeCases:
    """Tests for simplify_shape edge cases."""

    def test_empty_shapes(self) -> None:
        """Test simplifying empty shapes."""
        shapes: list[list[list[tuple[float, float]]]] = []

        result = simplify_shape(shapes, FillRule.EvenOdd)
        result_geom = shapes_to_multipolygon(result)

        assert result_geom.is_empty

    def test_single_triangle(self) -> None:
        """Test simplifying a single triangle."""
        triangle = [[[(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)]]]

        result = simplify_shape(triangle, FillRule.EvenOdd)
        result_geom = shapes_to_multipolygon(result)

        expected = shapely.Polygon([(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)])
        assert result_geom.equals(expected)
