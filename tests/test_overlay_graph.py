"""Tests for FloatOverlayGraph class."""

import math

import pytest
import shapely

from i_overlay import (
    FillRule,
    FloatOverlayGraph,
    OverlayOptions,
    OverlayRule,
    Solver,
)

from .shapely_utils import box, shapes_to_multipolygon


class TestFloatOverlayGraphBasic:
    """Basic tests for FloatOverlayGraph."""

    def test_create_overlay_graph(self) -> None:
        """Test creating an FloatOverlayGraph."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd)

        assert graph is not None

    def test_extract_union(self) -> None:
        """Test extracting union from graph."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd)
        result = graph.extract_shapes(OverlayRule.Union)
        result_geom = shapes_to_multipolygon(result)

        expected = shapely.box(0.0, 0.0, 2.0, 2.0).union(shapely.box(1.0, 1.0, 3.0, 3.0))
        assert result_geom.equals(expected)

    def test_extract_intersection(self) -> None:
        """Test extracting intersection from graph."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd)
        result = graph.extract_shapes(OverlayRule.Intersect)
        result_geom = shapes_to_multipolygon(result)

        # 1x1 square at (1,1) to (2,2)
        expected = shapely.box(1.0, 1.0, 2.0, 2.0)
        assert result_geom.equals(expected)

    def test_extract_difference(self) -> None:
        """Test extracting difference from graph."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd)
        result = graph.extract_shapes(OverlayRule.Difference)
        result_geom = shapes_to_multipolygon(result)

        expected = shapely.box(0.0, 0.0, 2.0, 2.0).difference(shapely.box(1.0, 1.0, 3.0, 3.0))
        assert result_geom.equals(expected)

    def test_extract_xor(self) -> None:
        """Test extracting XOR from graph."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd)
        result = graph.extract_shapes(OverlayRule.Xor)
        result_geom = shapes_to_multipolygon(result)

        expected = shapely.box(0.0, 0.0, 2.0, 2.0).symmetric_difference(shapely.box(1.0, 1.0, 3.0, 3.0))
        assert result_geom.equals(expected)


class TestFloatOverlayGraphMultipleExtractions:
    """Tests for extracting multiple results from the same graph."""

    def test_extract_all_operations(self) -> None:
        """Test extracting all Boolean operations from the same graph."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd)

        # Build expected results using shapely
        subj_geom = shapely.box(0.0, 0.0, 2.0, 2.0)
        clip_geom = shapely.box(1.0, 1.0, 3.0, 3.0)

        # Extract all operations from the same graph
        union = graph.extract_shapes(OverlayRule.Union)
        assert shapes_to_multipolygon(union).equals(subj_geom.union(clip_geom))

        intersection = graph.extract_shapes(OverlayRule.Intersect)
        assert shapes_to_multipolygon(intersection).equals(subj_geom.intersection(clip_geom))

        difference = graph.extract_shapes(OverlayRule.Difference)
        assert shapes_to_multipolygon(difference).equals(subj_geom.difference(clip_geom))

        inverse_diff = graph.extract_shapes(OverlayRule.InverseDifference)
        assert shapes_to_multipolygon(inverse_diff).equals(clip_geom.difference(subj_geom))

        xor = graph.extract_shapes(OverlayRule.Xor)
        assert shapes_to_multipolygon(xor).equals(subj_geom.symmetric_difference(clip_geom))

    def test_extract_same_operation_twice(self) -> None:
        """Test that extracting the same operation twice gives consistent results."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd)

        result1 = graph.extract_shapes(OverlayRule.Union)
        result2 = graph.extract_shapes(OverlayRule.Union)

        # Results should be geometrically equal
        assert shapes_to_multipolygon(result1).equals(shapes_to_multipolygon(result2))


class TestFloatOverlayGraphWithOptions:
    """Tests for FloatOverlayGraph with custom options."""

    def test_with_overlay_options(self) -> None:
        """Test FloatOverlayGraph with custom OverlayOptions."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        options = OverlayOptions(preserve_input_collinear=True)
        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd, options=options)

        result = graph.extract_shapes(OverlayRule.Union)
        result_geom = shapes_to_multipolygon(result)

        expected = shapely.box(0.0, 0.0, 2.0, 2.0).union(shapely.box(1.0, 1.0, 3.0, 3.0))
        assert result_geom.equals(expected)

    def test_with_solver(self) -> None:
        """Test FloatOverlayGraph with custom Solver."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        solver = Solver.AUTO
        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd, solver=solver)

        result = graph.extract_shapes(OverlayRule.Union)
        result_geom = shapes_to_multipolygon(result)

        expected = shapely.box(0.0, 0.0, 2.0, 2.0).union(shapely.box(1.0, 1.0, 3.0, 3.0))
        assert result_geom.equals(expected)

    def test_with_all_options(self) -> None:
        """Test FloatOverlayGraph with all options specified."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        options = OverlayOptions(preserve_input_collinear=True)
        solver = Solver.TREE
        graph = FloatOverlayGraph(subject, clip, FillRule.NonZero, options=options, solver=solver)

        result = graph.extract_shapes(OverlayRule.Union)
        result_geom = shapes_to_multipolygon(result)

        expected = shapely.box(0.0, 0.0, 2.0, 2.0).union(shapely.box(1.0, 1.0, 3.0, 3.0))
        assert result_geom.equals(expected)


class TestFloatOverlayGraphFillRules:
    """Tests for FloatOverlayGraph with different fill rules."""

    def test_even_odd_fill_rule(self) -> None:
        """Test FloatOverlayGraph with EvenOdd fill rule."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd)
        result = graph.extract_shapes(OverlayRule.Union)
        result_geom = shapes_to_multipolygon(result)

        expected = shapely.box(0.0, 0.0, 2.0, 2.0).union(shapely.box(1.0, 1.0, 3.0, 3.0))
        assert result_geom.equals(expected)

    def test_nonzero_fill_rule(self) -> None:
        """Test FloatOverlayGraph with NonZero fill rule."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        graph = FloatOverlayGraph(subject, clip, FillRule.NonZero)
        result = graph.extract_shapes(OverlayRule.Union)
        result_geom = shapes_to_multipolygon(result)

        expected = shapely.box(0.0, 0.0, 2.0, 2.0).union(shapely.box(1.0, 1.0, 3.0, 3.0))
        assert result_geom.equals(expected)


class TestFloatOverlayGraphEdgeCases:
    """Tests for FloatOverlayGraph edge cases."""

    def test_empty_subject(self) -> None:
        """Test FloatOverlayGraph with empty subject."""
        subject: list[list[list[tuple[float, float]]]] = []
        clip = box(0.0, 0.0, 1.0, 1.0)

        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd)
        result = graph.extract_shapes(OverlayRule.Union)
        result_geom = shapes_to_multipolygon(result)

        # Clip should pass through
        expected = shapely.box(0.0, 0.0, 1.0, 1.0)
        assert result_geom.equals(expected)

    def test_empty_clip(self) -> None:
        """Test FloatOverlayGraph with empty clip."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip: list[list[list[tuple[float, float]]]] = []

        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd)
        result = graph.extract_shapes(OverlayRule.Union)
        result_geom = shapes_to_multipolygon(result)

        # Subject should pass through
        expected = shapely.box(0.0, 0.0, 1.0, 1.0)
        assert result_geom.equals(expected)

    def test_no_overlap(self) -> None:
        """Test FloatOverlayGraph when shapes don't overlap."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip = box(5.0, 0.0, 6.0, 1.0)

        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd)

        # Union should have both shapes
        union = graph.extract_shapes(OverlayRule.Union)
        union_geom = shapes_to_multipolygon(union)
        expected_union = shapely.box(0.0, 0.0, 1.0, 1.0).union(shapely.box(5.0, 0.0, 6.0, 1.0))
        assert union_geom.equals(expected_union)

        # Intersection should be empty
        intersection = graph.extract_shapes(OverlayRule.Intersect)
        assert shapes_to_multipolygon(intersection).is_empty


class TestFloatOverlayGraphRepr:
    """Tests for FloatOverlayGraph repr."""

    def test_repr(self) -> None:
        """Test repr representation."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd)
        r = repr(graph)

        assert "FloatOverlayGraph" in r
        assert "subject_count=1" in r
        assert "clip_count=1" in r


class TestFloatOverlayGraphScale:
    """Tests for FloatOverlayGraph with scale parameter."""

    def test_with_scale(self) -> None:
        """Test FloatOverlayGraph with explicit scale."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd, scale=1000.0)
        result = graph.extract_shapes(OverlayRule.Union)
        result_geom = shapes_to_multipolygon(result)

        expected = shapely.box(0.0, 0.0, 2.0, 2.0).union(shapely.box(1.0, 1.0, 3.0, 3.0))
        assert result_geom.equals(expected)

    def test_with_scale_multiple_extractions(self) -> None:
        """Test multiple extractions with fixed scale."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd, scale=1000.0)

        subj_geom = shapely.box(0.0, 0.0, 2.0, 2.0)
        clip_geom = shapely.box(1.0, 1.0, 3.0, 3.0)

        union = graph.extract_shapes(OverlayRule.Union)
        assert shapes_to_multipolygon(union).equals(subj_geom.union(clip_geom))

        intersection = graph.extract_shapes(OverlayRule.Intersect)
        assert shapes_to_multipolygon(intersection).equals(subj_geom.intersection(clip_geom))

    def test_with_scale_and_options(self) -> None:
        """Test FloatOverlayGraph with scale and options."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        options = OverlayOptions(preserve_input_collinear=True)
        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd, options=options, scale=1000.0)

        result = graph.extract_shapes(OverlayRule.Union)
        result_geom = shapes_to_multipolygon(result)

        expected = shapely.box(0.0, 0.0, 2.0, 2.0).union(shapely.box(1.0, 1.0, 3.0, 3.0))
        assert result_geom.equals(expected)

    def test_with_scale_and_solver(self) -> None:
        """Test FloatOverlayGraph with scale and solver."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd, solver=Solver.LIST, scale=1000.0)

        result = graph.extract_shapes(OverlayRule.Union)
        result_geom = shapes_to_multipolygon(result)

        expected = shapely.box(0.0, 0.0, 2.0, 2.0).union(shapely.box(1.0, 1.0, 3.0, 3.0))
        assert result_geom.equals(expected)

    def test_scale_invalid_negative(self) -> None:
        """Test that negative scale raises ValueError."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip = box(0.5, 0.0, 1.5, 1.0)

        with pytest.raises(ValueError, match="scale must be positive"):
            FloatOverlayGraph(subject, clip, FillRule.EvenOdd, scale=-1.0)

    def test_scale_invalid_zero(self) -> None:
        """Test that zero scale raises ValueError."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip = box(0.5, 0.0, 1.5, 1.0)

        with pytest.raises(ValueError, match="scale must be positive"):
            FloatOverlayGraph(subject, clip, FillRule.EvenOdd, scale=0.0)

    def test_scale_invalid_nan(self) -> None:
        """Test that NaN scale raises ValueError."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip = box(0.5, 0.0, 1.5, 1.0)

        with pytest.raises(ValueError, match="scale must be finite"):
            FloatOverlayGraph(subject, clip, FillRule.EvenOdd, scale=math.nan)

    def test_scale_invalid_infinity(self) -> None:
        """Test that infinity scale raises ValueError."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip = box(0.5, 0.0, 1.5, 1.0)

        with pytest.raises(ValueError, match="scale must be finite"):
            FloatOverlayGraph(subject, clip, FillRule.EvenOdd, scale=math.inf)

    def test_scale_too_large(self) -> None:
        """Test that excessively large scale raises ValueError during extraction."""
        subject = box(0.0, 0.0, 1.0, 1.0)
        clip = box(0.5, 0.0, 1.5, 1.0)

        # Scale too large error is detected when creating the FloatOverlay,
        # which happens during extract_shapes() rather than construction
        huge_scale = float(1 << 32)
        graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd, scale=huge_scale)
        with pytest.raises(ValueError, match="scale too large"):
            graph.extract_shapes(OverlayRule.Union)

    def test_scale_produces_same_result_as_auto(self) -> None:
        """Test that scale produces equivalent results to auto-scaling."""
        subject = box(0.0, 0.0, 2.0, 2.0)
        clip = box(1.0, 1.0, 3.0, 3.0)

        auto_graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd)
        scaled_graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd, scale=1000.0)

        auto_result = auto_graph.extract_shapes(OverlayRule.Union)
        scaled_result = scaled_graph.extract_shapes(OverlayRule.Union)

        assert shapes_to_multipolygon(auto_result).equals(shapes_to_multipolygon(scaled_result))
