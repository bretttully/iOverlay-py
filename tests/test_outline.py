"""Tests for outline function."""

from i_overlay import (
    LineJoin,
    OutlineStyle,
    OverlayOptions,
    outline,
)

from .shapely_utils import shapes_to_multipolygon


class TestOutlineBasic:
    """Basic tests for outline function."""

    def test_outline_square(self) -> None:
        """Test outlining a square."""
        # Counter-clockwise square (outer boundary)
        shapes = [[[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]]]
        style = OutlineStyle(1.0)

        result = outline(shapes, style)
        result_geom = shapes_to_multipolygon(result)

        assert len(result) == 1
        assert result_geom.is_valid
        # Outline should expand the shape

    def test_outline_triangle(self) -> None:
        """Test outlining a triangle."""
        # Counter-clockwise triangle
        shapes = [[[(0.0, 0.0), (10.0, 0.0), (5.0, 10.0)]]]
        style = OutlineStyle(1.0)

        result = outline(shapes, style)
        result_geom = shapes_to_multipolygon(result)

        assert len(result) == 1
        assert result_geom.is_valid


class TestOutlineWithHoles:
    """Tests for outlining shapes with holes."""

    def test_outline_square_with_hole(self) -> None:
        """Test outlining a square with a hole."""
        # Outer boundary (counter-clockwise) with inner hole (clockwise)
        shapes = [
            [
                [(0.0, 0.0), (20.0, 0.0), (20.0, 20.0), (0.0, 20.0)],
                [(5.0, 5.0), (5.0, 15.0), (15.0, 15.0), (15.0, 5.0)],
            ]
        ]
        style = OutlineStyle(1.0)

        result = outline(shapes, style)
        result_geom = shapes_to_multipolygon(result)

        assert result_geom.is_valid


class TestOutlineStyles:
    """Tests for different outline styles."""

    def test_outline_round_join(self) -> None:
        """Test outline with round joins."""
        shapes = [[[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]]]
        style = OutlineStyle(1.0, join=LineJoin.Round)

        result = outline(shapes, style)
        result_geom = shapes_to_multipolygon(result)

        assert result_geom.is_valid

    def test_outline_miter_join(self) -> None:
        """Test outline with miter joins."""
        shapes = [[[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]]]
        style = OutlineStyle(1.0, join=LineJoin.Miter)

        result = outline(shapes, style)
        result_geom = shapes_to_multipolygon(result)

        assert result_geom.is_valid

    def test_outline_asymmetric_offsets(self) -> None:
        """Test outline with different inner and outer offsets."""
        shapes = [[[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]]]
        style = OutlineStyle(offset=1.0, outer_offset=2.0, inner_offset=0.5)

        result = outline(shapes, style)
        result_geom = shapes_to_multipolygon(result)

        assert result_geom.is_valid


class TestOutlineWithOptions:
    """Tests for outline with custom options."""

    def test_outline_with_options(self) -> None:
        """Test outline with custom overlay options."""
        shapes = [[[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]]]
        style = OutlineStyle(1.0)
        options = OverlayOptions(preserve_output_collinear=True)

        result = outline(shapes, style, options=options)
        result_geom = shapes_to_multipolygon(result)

        assert result_geom.is_valid


class TestOutlineEdgeCases:
    """Tests for outline edge cases."""

    def test_outline_empty_shapes(self) -> None:
        """Test outlining empty shapes."""
        shapes: list[list[list[tuple[float, float]]]] = []
        style = OutlineStyle(1.0)

        result = outline(shapes, style)

        assert len(result) == 0

    def test_outline_clockwise_shape(self) -> None:
        """Test outlining a clockwise shape (should be treated as hole)."""
        # Clockwise shape - should not produce output
        shapes = [[[(0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, 0.0)]]]
        style = OutlineStyle(1.0)

        result = outline(shapes, style)

        # Clockwise shapes are treated as holes and produce no output
        assert len(result) == 0

    def test_outline_large_offset(self) -> None:
        """Test outline with offset larger than shape."""
        shapes = [[[(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]]]
        style = OutlineStyle(10.0)

        result = outline(shapes, style)

        # Large negative offset may eliminate the shape
        # Just verify it doesn't crash
        assert isinstance(result, list)


class TestOutlineStyleClass:
    """Tests for OutlineStyle class."""

    def test_outline_style_defaults(self) -> None:
        """Test OutlineStyle with default offset."""
        style = OutlineStyle(2.0)

        assert style.outer_offset == 2.0
        assert style.inner_offset == 2.0
        assert style.join == LineJoin.Bevel

    def test_outline_style_custom(self) -> None:
        """Test OutlineStyle with custom values."""
        style = OutlineStyle(
            offset=1.0,
            outer_offset=3.0,
            inner_offset=1.5,
            join=LineJoin.Round,
        )

        assert style.outer_offset == 3.0
        assert style.inner_offset == 1.5
        assert style.join == LineJoin.Round

    def test_outline_style_repr(self) -> None:
        """Test OutlineStyle string representation."""
        style = OutlineStyle(2.0)
        repr_str = repr(style)

        assert "OutlineStyle" in repr_str
        assert "2" in repr_str
