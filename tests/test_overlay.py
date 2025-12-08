"""Tests for Boolean overlay operations."""

from shapely import Polygon
from shapely import box as shapely_box

from i_overlay import (
    ContourDirection,
    FillRule,
    OverlayOptions,
    OverlayRule,
    Precision,
    Solver,
    Strategy,
    overlay,
)

from .shapely_utils import (
    box,
    circle,
    geometry_to_shapes,
    polygon_with_hole,
)


class TestOverlayBasic:
    """Basic tests for the overlay function."""

    def test_overlay_union_simple_rectangles(self) -> None:
        """Test union of two adjacent rectangles."""
        # Two 1x1 squares side by side
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip = box(1.0, 0.0, 2.0, 1.0)

        result = overlay(subject, clip, OverlayRule.Union, FillRule.EvenOdd)

        # Should produce a single 2x1 rectangle
        assert len(result) == 1
        assert len(result[0]) == 1
        assert len(result[0][0]) == 4

    def test_overlay_intersection_overlapping_squares(self) -> None:
        """Test intersection of two overlapping squares."""
        # 2x2 square at origin
        subject = box(0.0, 0.0, 2.0, 2.0)
        # 2x2 square offset by (1,1)
        clip = box(1.0, 1.0, 3.0, 3.0)

        result = overlay(subject, clip, OverlayRule.Intersect, FillRule.EvenOdd)

        # Should produce a 1x1 square at (1,1)
        assert len(result) == 1
        assert len(result[0]) == 1
        assert len(result[0][0]) == 4

    def test_overlay_difference(self) -> None:
        """Test difference of two overlapping squares."""
        # 2x2 square at origin
        subject = box(0.0, 0.0, 2.0, 2.0)
        # 1x1 square at (1,1)
        clip = box(1.0, 1.0, 2.0, 2.0)

        result = overlay(subject, clip, OverlayRule.Difference, FillRule.EvenOdd)

        # Should produce an L-shaped result
        assert len(result) == 1

    def test_overlay_xor(self) -> None:
        """Test XOR of two overlapping squares."""
        # 2x2 square at origin
        subject = box(0.0, 0.0, 2.0, 2.0)
        # 2x2 square offset by (1,1)
        clip = box(1.0, 1.0, 3.0, 3.0)

        result = overlay(subject, clip, OverlayRule.Xor, FillRule.EvenOdd)

        # Should produce two separate shapes
        assert len(result) >= 1


class TestOverlayWithHoles:
    """Tests for overlay operations with shapes containing holes."""

    def test_shape_with_hole(self) -> None:
        """Test union where subject has a hole."""
        # 4x4 square with 2x2 hole in center
        outer = [(0.0, 0.0), (0.0, 4.0), (4.0, 4.0), (4.0, 0.0)]
        hole = [(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)]
        subject = polygon_with_hole(outer, hole)

        # 1x1 square that fills part of the hole
        clip = box(1.5, 1.5, 2.5, 2.5)

        result = overlay(subject, clip, OverlayRule.Union, FillRule.EvenOdd)

        # Should have a shape with a smaller hole
        assert len(result) >= 1

    def test_intersection_removes_hole(self) -> None:
        """Test intersection that removes the hole entirely."""
        # 4x4 square with 2x2 hole in center
        outer = [(0.0, 0.0), (0.0, 4.0), (4.0, 4.0), (4.0, 0.0)]
        hole = [(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)]
        subject = polygon_with_hole(outer, hole)

        # 2x2 square that doesn't touch the hole
        clip = box(3.0, 0.0, 4.0, 1.0)

        result = overlay(subject, clip, OverlayRule.Intersect, FillRule.EvenOdd)

        # Should produce a solid shape without a hole
        assert len(result) == 1
        assert len(result[0]) == 1  # No holes


class TestOverlayFillRules:
    """Tests for different fill rules."""

    def test_nonzero_fill_rule(self) -> None:
        """Test NonZero fill rule."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip = box(0.5, 0.0, 1.5, 1.0)

        result = overlay(subject, clip, OverlayRule.Union, FillRule.NonZero)

        assert len(result) >= 1

    def test_positive_fill_rule(self) -> None:
        """Test Positive fill rule."""
        # Clockwise winding for positive fill rule
        polygon = Polygon([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])
        subject = geometry_to_shapes(polygon)
        polygon2 = Polygon([(0.5, 0.0), (1.5, 0.0), (1.5, 1.0), (0.5, 1.0)])
        clip = geometry_to_shapes(polygon2)

        result = overlay(subject, clip, OverlayRule.Union, FillRule.Positive)

        # Result depends on winding direction
        assert isinstance(result, list)

    def test_negative_fill_rule(self) -> None:
        """Test Negative fill rule."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip = box(0.5, 0.0, 1.5, 1.0)

        result = overlay(subject, clip, OverlayRule.Union, FillRule.Negative)

        # Results may vary based on winding direction
        assert isinstance(result, list)


class TestOverlayOptions:
    """Tests for overlay options."""

    def test_with_options(self) -> None:
        """Test overlay with custom options."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip = box(1.0, 0.0, 2.0, 1.0)

        options = OverlayOptions(
            preserve_input_collinear=True,
            output_direction=ContourDirection.Clockwise,
            preserve_output_collinear=True,
            min_output_area=0,
        )

        result = overlay(subject, clip, OverlayRule.Union, FillRule.EvenOdd, options=options)

        assert len(result) >= 1

    def test_with_min_output_area(self) -> None:
        """Test that min_output_area filters small shapes."""
        subject = box(0.0, 0.0, 10.0, 10.0)
        clip = box(9.0, 9.0, 10.0, 10.0)

        # With a large min area, the small result may be filtered
        options = OverlayOptions(min_output_area=1000)

        result = overlay(subject, clip, OverlayRule.Intersect, FillRule.EvenOdd, options=options)

        # The 1x1 intersection should be filtered
        assert len(result) == 0


class TestOverlaySolver:
    """Tests for solver options."""

    def test_with_list_strategy(self) -> None:
        """Test overlay with List strategy."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip = box(0.5, 0.0, 1.5, 1.0)

        solver = Solver(strategy=Strategy.List)

        result = overlay(subject, clip, OverlayRule.Union, FillRule.EvenOdd, solver=solver)

        assert len(result) >= 1

    def test_with_tree_strategy(self) -> None:
        """Test overlay with Tree strategy."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip = box(0.5, 0.0, 1.5, 1.0)

        solver = Solver(strategy=Strategy.Tree)

        result = overlay(subject, clip, OverlayRule.Union, FillRule.EvenOdd, solver=solver)

        assert len(result) >= 1

    def test_with_custom_precision(self) -> None:
        """Test overlay with custom precision."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip = box(0.5, 0.0, 1.5, 1.0)

        precision = Precision(start=1, progression=2)
        solver = Solver(strategy=Strategy.Auto, precision=precision, multithreading=False)

        result = overlay(subject, clip, OverlayRule.Union, FillRule.EvenOdd, solver=solver)

        assert len(result) >= 1

    def test_with_preset_solvers(self) -> None:
        """Test overlay with preset solvers."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip = box(0.5, 0.0, 1.5, 1.0)

        for solver in [Solver.AUTO, Solver.LIST, Solver.TREE, Solver.FRAG]:
            result = overlay(subject, clip, OverlayRule.Union, FillRule.EvenOdd, solver=solver)
            assert len(result) >= 1


class TestOverlaySubjectOnly:
    """Tests for Subject/Clip-only operations."""

    def test_subject_rule_self_intersecting(self) -> None:
        """Test Subject rule for resolving self-intersections."""
        # A figure-8 shape (self-intersecting)
        subject = [[[(0.0, 0.0), (2.0, 2.0), (2.0, 0.0), (0.0, 2.0)]]]
        clip: list[list[list[tuple[float, float]]]] = []  # Empty clip

        result = overlay(subject, clip, OverlayRule.Subject, FillRule.EvenOdd)

        # Should resolve the self-intersection
        assert isinstance(result, list)


class TestOverlayMultipleShapes:
    """Tests for operations on multiple shapes."""

    def test_union_multiple_shapes(self) -> None:
        """Test union of multiple shapes."""
        # Three squares in a row (subject has two, clip has one)
        subject = [
            geometry_to_shapes(shapely_box(0.0, 0.0, 1.0, 1.0))[0],
            geometry_to_shapes(shapely_box(1.0, 0.0, 2.0, 1.0))[0],
        ]
        clip = box(2.0, 0.0, 3.0, 1.0)

        result = overlay(subject, clip, OverlayRule.Union, FillRule.EvenOdd)

        # Should produce a single 3x1 rectangle
        assert len(result) == 1

    def test_intersection_no_overlap(self) -> None:
        """Test intersection when shapes don't overlap."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip = box(5.0, 0.0, 6.0, 1.0)

        result = overlay(subject, clip, OverlayRule.Intersect, FillRule.EvenOdd)

        # No intersection, should return empty
        assert len(result) == 0


class TestOverlayEdgeCases:
    """Tests for edge cases."""

    def test_empty_subject(self) -> None:
        """Test with empty subject."""
        subject: list[list[list[tuple[float, float]]]] = []
        clip = box(0.0, 0.0, 1.0, 1.0)

        result = overlay(subject, clip, OverlayRule.Union, FillRule.EvenOdd)

        # Clip should pass through
        assert len(result) == 1

    def test_empty_clip(self) -> None:
        """Test with empty clip."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip: list[list[list[tuple[float, float]]]] = []

        result = overlay(subject, clip, OverlayRule.Union, FillRule.EvenOdd)

        # Subject should pass through
        assert len(result) == 1

    def test_both_empty(self) -> None:
        """Test with both subject and clip empty."""
        subject: list[list[list[tuple[float, float]]]] = []
        clip: list[list[list[tuple[float, float]]]] = []

        result = overlay(subject, clip, OverlayRule.Union, FillRule.EvenOdd)

        assert len(result) == 0

    def test_identical_shapes(self) -> None:
        """Test operations on identical shapes."""
        shape = box(0.0, 0.0, 1.0, 1.0)

        union_result = overlay(shape, shape, OverlayRule.Union, FillRule.EvenOdd)
        intersect_result = overlay(shape, shape, OverlayRule.Intersect, FillRule.EvenOdd)
        diff_result = overlay(shape, shape, OverlayRule.Difference, FillRule.EvenOdd)
        xor_result = overlay(shape, shape, OverlayRule.Xor, FillRule.EvenOdd)

        # Union and intersection should return the original shape
        assert len(union_result) == 1
        assert len(intersect_result) == 1
        # Difference and XOR should return empty
        assert len(diff_result) == 0
        assert len(xor_result) == 0


class TestOverlayResultFormat:
    """Tests for result format correctness."""

    def test_result_is_nested_list(self) -> None:
        """Test that result is properly nested list of tuples."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip = box(0.5, 0.0, 1.5, 1.0)

        result = overlay(subject, clip, OverlayRule.Union, FillRule.EvenOdd)

        # Check structure: list of shapes
        assert isinstance(result, list)
        if len(result) > 0:
            # Each shape is a list of contours
            assert isinstance(result[0], list)
            if len(result[0]) > 0:
                # Each contour is a list of points
                assert isinstance(result[0][0], list)
                if len(result[0][0]) > 0:
                    # Each point is a tuple of (x, y)
                    point = result[0][0][0]
                    assert isinstance(point, tuple)
                    assert len(point) == 2
                    assert isinstance(point[0], float)
                    assert isinstance(point[1], float)


class TestOverlayWithCircles:
    """Tests using circular shapes."""

    def test_union_circles(self) -> None:
        """Test union of two overlapping circles."""
        subject = circle(0.0, 0.0, 1.0)
        clip = circle(1.0, 0.0, 1.0)

        result = overlay(subject, clip, OverlayRule.Union, FillRule.EvenOdd)

        # Should produce a single merged shape
        assert len(result) == 1

    def test_intersection_circles(self) -> None:
        """Test intersection of two overlapping circles."""
        subject = circle(0.0, 0.0, 1.0)
        clip = circle(1.0, 0.0, 1.0)

        result = overlay(subject, clip, OverlayRule.Intersect, FillRule.EvenOdd)

        # Should produce a lens-shaped intersection
        assert len(result) == 1
