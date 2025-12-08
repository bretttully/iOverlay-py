"""Tests for enum types."""

from i_overlay import (
    ContourDirection,
    FillRule,
    LineCap,
    LineJoin,
    OverlayRule,
    ShapeType,
    Strategy,
)


class TestFillRule:
    """Tests for FillRule enum."""

    def test_variants_exist(self) -> None:
        """Test that all variants are accessible."""
        assert FillRule.EvenOdd is not None
        assert FillRule.NonZero is not None
        assert FillRule.Positive is not None
        assert FillRule.Negative is not None

    def test_equality(self) -> None:
        """Test enum equality."""
        assert FillRule.EvenOdd == FillRule.EvenOdd
        assert FillRule.NonZero == FillRule.NonZero
        assert FillRule.EvenOdd != FillRule.NonZero

    def test_repr(self) -> None:
        """Test repr representation."""
        assert repr(FillRule.EvenOdd) == "FillRule.EvenOdd"
        assert repr(FillRule.NonZero) == "FillRule.NonZero"
        assert repr(FillRule.Positive) == "FillRule.Positive"
        assert repr(FillRule.Negative) == "FillRule.Negative"

    def test_hashable(self) -> None:
        """Test that enums are hashable (can be used in sets/dicts)."""
        fill_rules = {FillRule.EvenOdd, FillRule.NonZero}
        assert len(fill_rules) == 2
        assert FillRule.EvenOdd in fill_rules


class TestOverlayRule:
    """Tests for OverlayRule enum."""

    def test_variants_exist(self) -> None:
        """Test that all variants are accessible."""
        assert OverlayRule.Subject is not None
        assert OverlayRule.Clip is not None
        assert OverlayRule.Intersect is not None
        assert OverlayRule.Union is not None
        assert OverlayRule.Difference is not None
        assert OverlayRule.InverseDifference is not None
        assert OverlayRule.Xor is not None

    def test_equality(self) -> None:
        """Test enum equality."""
        assert OverlayRule.Union == OverlayRule.Union
        assert OverlayRule.Union != OverlayRule.Intersect

    def test_repr(self) -> None:
        """Test repr representation."""
        assert repr(OverlayRule.Subject) == "OverlayRule.Subject"
        assert repr(OverlayRule.Clip) == "OverlayRule.Clip"
        assert repr(OverlayRule.Intersect) == "OverlayRule.Intersect"
        assert repr(OverlayRule.Union) == "OverlayRule.Union"
        assert repr(OverlayRule.Difference) == "OverlayRule.Difference"
        assert repr(OverlayRule.InverseDifference) == "OverlayRule.InverseDifference"
        assert repr(OverlayRule.Xor) == "OverlayRule.Xor"


class TestContourDirection:
    """Tests for ContourDirection enum."""

    def test_variants_exist(self) -> None:
        """Test that all variants are accessible."""
        assert ContourDirection.CounterClockwise is not None
        assert ContourDirection.Clockwise is not None

    def test_repr(self) -> None:
        """Test repr representation."""
        assert repr(ContourDirection.CounterClockwise) == "ContourDirection.CounterClockwise"
        assert repr(ContourDirection.Clockwise) == "ContourDirection.Clockwise"


class TestShapeType:
    """Tests for ShapeType enum."""

    def test_variants_exist(self) -> None:
        """Test that all variants are accessible."""
        assert ShapeType.Subject is not None
        assert ShapeType.Clip is not None

    def test_repr(self) -> None:
        """Test repr representation."""
        assert repr(ShapeType.Subject) == "ShapeType.Subject"
        assert repr(ShapeType.Clip) == "ShapeType.Clip"


class TestStrategy:
    """Tests for Strategy enum."""

    def test_variants_exist(self) -> None:
        """Test that all variants are accessible."""
        assert Strategy.List is not None
        assert Strategy.Tree is not None
        assert Strategy.Frag is not None
        assert Strategy.Auto is not None

    def test_repr(self) -> None:
        """Test repr representation."""
        assert repr(Strategy.List) == "Strategy.List"
        assert repr(Strategy.Tree) == "Strategy.Tree"
        assert repr(Strategy.Frag) == "Strategy.Frag"
        assert repr(Strategy.Auto) == "Strategy.Auto"


class TestLineCap:
    """Tests for LineCap enum."""

    def test_variants_exist(self) -> None:
        """Test that all variants are accessible."""
        assert LineCap.Butt is not None
        assert LineCap.Round is not None
        assert LineCap.Square is not None

    def test_repr(self) -> None:
        """Test repr representation."""
        assert repr(LineCap.Butt) == "LineCap.Butt"
        assert repr(LineCap.Round) == "LineCap.Round"
        assert repr(LineCap.Square) == "LineCap.Square"


class TestLineJoin:
    """Tests for LineJoin enum."""

    def test_variants_exist(self) -> None:
        """Test that all variants are accessible."""
        assert LineJoin.Bevel is not None
        assert LineJoin.Miter is not None
        assert LineJoin.Round is not None

    def test_repr(self) -> None:
        """Test repr representation."""
        assert repr(LineJoin.Bevel) == "LineJoin.Bevel"
        assert repr(LineJoin.Miter) == "LineJoin.Miter"
        assert repr(LineJoin.Round) == "LineJoin.Round"
