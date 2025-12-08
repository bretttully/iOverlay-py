"""Tests for stroke function."""

from i_overlay import (
    LineCap,
    LineJoin,
    OverlayOptions,
    StrokeStyle,
    stroke,
)

from .shapely_utils import shapes_to_multipolygon


class TestStrokeBasic:
    """Basic tests for stroke function."""

    def test_stroke_simple_line(self) -> None:
        """Test stroking a simple horizontal line."""
        paths = [[(0.0, 0.0), (10.0, 0.0)]]
        style = StrokeStyle(2.0)

        result = stroke(paths, style)
        result_geom = shapes_to_multipolygon(result)

        # Should produce a rectangle-like shape
        assert len(result) == 1
        assert result_geom.is_valid
        # Width is 2, so area should be approximately 10 * 2 = 20
        assert abs(result_geom.area - 20.0) < 1.0

    def test_stroke_l_shape(self) -> None:
        """Test stroking an L-shaped path."""
        paths = [[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]]
        style = StrokeStyle(2.0)

        result = stroke(paths, style)
        result_geom = shapes_to_multipolygon(result)

        assert len(result) == 1
        assert result_geom.is_valid

    def test_stroke_closed_path(self) -> None:
        """Test stroking a closed square path."""
        paths = [[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]]
        style = StrokeStyle(2.0)

        result = stroke(paths, style, is_closed=True)
        result_geom = shapes_to_multipolygon(result)

        # Closed path should produce a shape with a hole
        assert len(result) == 1
        assert result_geom.is_valid
        # Should have outer boundary and inner hole
        assert len(result[0]) == 2


class TestStrokeStyles:
    """Tests for different stroke styles."""

    def test_stroke_round_caps(self) -> None:
        """Test stroking with round caps."""
        paths = [[(0.0, 0.0), (10.0, 0.0)]]
        style = StrokeStyle(2.0, start_cap=LineCap.Round, end_cap=LineCap.Round)

        result = stroke(paths, style)
        result_geom = shapes_to_multipolygon(result)

        assert len(result) == 1
        assert result_geom.is_valid
        # Round caps add semicircles at each end
        # Area should be slightly more than butt caps

    def test_stroke_square_caps(self) -> None:
        """Test stroking with square caps."""
        paths = [[(0.0, 0.0), (10.0, 0.0)]]
        style = StrokeStyle(2.0, start_cap=LineCap.Square, end_cap=LineCap.Square)

        result = stroke(paths, style)
        result_geom = shapes_to_multipolygon(result)

        assert len(result) == 1
        assert result_geom.is_valid
        # Square caps extend by half width at each end
        # Area should be (10 + 2) * 2 = 24
        assert abs(result_geom.area - 24.0) < 1.0

    def test_stroke_miter_join(self) -> None:
        """Test stroking with miter joins."""
        paths = [[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]]
        style = StrokeStyle(2.0, join=LineJoin.Miter)

        result = stroke(paths, style)
        result_geom = shapes_to_multipolygon(result)

        assert len(result) == 1
        assert result_geom.is_valid

    def test_stroke_round_join(self) -> None:
        """Test stroking with round joins."""
        paths = [[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]]
        style = StrokeStyle(2.0, join=LineJoin.Round)

        result = stroke(paths, style)
        result_geom = shapes_to_multipolygon(result)

        assert len(result) == 1
        assert result_geom.is_valid


class TestStrokeMultiplePaths:
    """Tests for stroking multiple paths."""

    def test_stroke_multiple_paths(self) -> None:
        """Test stroking multiple paths at once."""
        paths = [
            [(0.0, 0.0), (5.0, 0.0)],
            [(0.0, 5.0), (5.0, 5.0)],
        ]
        style = StrokeStyle(2.0)

        result = stroke(paths, style)
        result_geom = shapes_to_multipolygon(result)

        assert result_geom.is_valid
        # Two separate rectangles, each 5 * 2 = 10, total = 20
        assert abs(result_geom.area - 20.0) < 1.0


class TestStrokeWithOptions:
    """Tests for stroke with custom options."""

    def test_stroke_with_options(self) -> None:
        """Test stroke with custom overlay options."""
        paths = [[(0.0, 0.0), (10.0, 0.0)]]
        style = StrokeStyle(2.0)
        options = OverlayOptions(preserve_output_collinear=True)

        result = stroke(paths, style, options=options)
        result_geom = shapes_to_multipolygon(result)

        assert len(result) == 1
        assert result_geom.is_valid


class TestStrokeEdgeCases:
    """Tests for stroke edge cases."""

    def test_stroke_empty_paths(self) -> None:
        """Test stroking empty paths."""
        paths: list[list[tuple[float, float]]] = []
        style = StrokeStyle(2.0)

        result = stroke(paths, style)

        assert len(result) == 0

    def test_stroke_single_point(self) -> None:
        """Test stroking a single point path."""
        paths = [[(5.0, 5.0)]]
        style = StrokeStyle(2.0)

        result = stroke(paths, style)

        # Single point cannot create a stroke
        assert len(result) == 0

    def test_stroke_very_small_width(self) -> None:
        """Test stroking with very small width."""
        paths = [[(0.0, 0.0), (10.0, 0.0)]]
        style = StrokeStyle(0.001)

        result = stroke(paths, style)

        # Very small width may produce empty result due to precision
        # Just verify it doesn't crash
        assert isinstance(result, list)


class TestStrokeStyleClass:
    """Tests for StrokeStyle class."""

    def test_stroke_style_defaults(self) -> None:
        """Test StrokeStyle default values."""
        style = StrokeStyle(2.0)

        assert style.width == 2.0
        assert style.start_cap == LineCap.Butt
        assert style.end_cap == LineCap.Butt
        assert style.join == LineJoin.Bevel

    def test_stroke_style_custom(self) -> None:
        """Test StrokeStyle with custom values."""
        style = StrokeStyle(
            3.0,
            start_cap=LineCap.Round,
            end_cap=LineCap.Square,
            join=LineJoin.Miter,
        )

        assert style.width == 3.0
        assert style.start_cap == LineCap.Round
        assert style.end_cap == LineCap.Square
        assert style.join == LineJoin.Miter

    def test_stroke_style_repr(self) -> None:
        """Test StrokeStyle string representation."""
        style = StrokeStyle(2.0)
        repr_str = repr(style)

        assert "StrokeStyle" in repr_str
        assert "2" in repr_str


class TestStrokeCustomCaps:
    """Tests for custom line caps."""

    def test_stroke_custom_start_cap(self) -> None:
        """Test stroking with custom start cap points."""
        paths = [[(0.0, 0.0), (10.0, 0.0)]]
        # Arrow-like custom cap (pointing back)
        custom_cap = [(0.0, -0.5), (-1.0, 0.0), (0.0, 0.5)]
        style = StrokeStyle(2.0, start_cap_points=custom_cap)

        result = stroke(paths, style)
        result_geom = shapes_to_multipolygon(result)

        assert len(result) == 1
        assert result_geom.is_valid

    def test_stroke_custom_end_cap(self) -> None:
        """Test stroking with custom end cap points."""
        paths = [[(0.0, 0.0), (10.0, 0.0)]]
        # Arrow-like custom cap (pointing forward)
        custom_cap = [(0.0, -0.5), (1.0, 0.0), (0.0, 0.5)]
        style = StrokeStyle(2.0, end_cap_points=custom_cap)

        result = stroke(paths, style)
        result_geom = shapes_to_multipolygon(result)

        assert len(result) == 1
        assert result_geom.is_valid

    def test_stroke_custom_both_caps(self) -> None:
        """Test stroking with custom caps on both ends."""
        paths = [[(0.0, 0.0), (10.0, 0.0)]]
        # Arrow start (pointing back)
        start_cap = [(0.0, -0.5), (-1.0, 0.0), (0.0, 0.5)]
        # Arrow end (pointing forward)
        end_cap = [(0.0, -0.5), (1.0, 0.0), (0.0, 0.5)]
        style = StrokeStyle(2.0, start_cap_points=start_cap, end_cap_points=end_cap)

        result = stroke(paths, style)
        result_geom = shapes_to_multipolygon(result)

        assert len(result) == 1
        assert result_geom.is_valid

    def test_stroke_custom_cap_triangle(self) -> None:
        """Test stroking with triangular custom cap."""
        paths = [[(0.0, 0.0), (10.0, 0.0)]]
        # Triangle cap
        triangle_cap = [(0.0, -0.5), (0.5, 0.0), (0.0, 0.5)]
        style = StrokeStyle(2.0, end_cap_points=triangle_cap)

        result = stroke(paths, style)
        result_geom = shapes_to_multipolygon(result)

        assert len(result) == 1
        assert result_geom.is_valid
