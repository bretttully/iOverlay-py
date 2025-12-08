"""Tests for configuration classes."""

from i_overlay import (
    ClipRule,
    ContourDirection,
    OverlayOptions,
    Precision,
    Solver,
    Strategy,
)


class TestPrecision:
    """Tests for Precision configuration class."""

    def test_default_construction(self) -> None:
        """Test creating Precision with default values."""
        p = Precision()
        assert p.start == 0
        assert p.progression == 1

    def test_custom_construction(self) -> None:
        """Test creating Precision with custom values."""
        p = Precision(start=2, progression=3)
        assert p.start == 2
        assert p.progression == 3

    def test_class_constants(self) -> None:
        """Test that class constants are accessible."""
        assert Precision.ABSOLUTE.start == 0
        assert Precision.ABSOLUTE.progression == 0

        assert Precision.HIGH.start == 0
        assert Precision.HIGH.progression == 1

        assert Precision.MEDIUM_HIGH.start == 1
        assert Precision.MEDIUM_HIGH.progression == 1

        assert Precision.MEDIUM.start == 0
        assert Precision.MEDIUM.progression == 2

        assert Precision.MEDIUM_LOW.start == 2
        assert Precision.MEDIUM_LOW.progression == 2

        assert Precision.LOW.start == 2
        assert Precision.LOW.progression == 3

    def test_equality(self) -> None:
        """Test Precision equality."""
        p1 = Precision(start=1, progression=2)
        p2 = Precision(start=1, progression=2)
        p3 = Precision(start=2, progression=2)
        assert p1 == p2
        assert p1 != p3

    def test_hashable(self) -> None:
        """Test that Precision is hashable."""
        p1 = Precision(start=1, progression=2)
        p2 = Precision(start=1, progression=2)
        precisions = {p1, p2}
        assert len(precisions) == 1

    def test_repr(self) -> None:
        """Test repr representation."""
        p = Precision(start=2, progression=3)
        assert repr(p) == "Precision(start=2, progression=3)"


class TestSolver:
    """Tests for Solver configuration class."""

    def test_default_construction(self) -> None:
        """Test creating Solver with default values."""
        s = Solver()
        assert s.strategy == Strategy.Auto
        assert s.precision == Precision.HIGH
        assert s.multithreading is True

    def test_custom_construction(self) -> None:
        """Test creating Solver with custom values."""
        p = Precision(start=2, progression=2)
        s = Solver(strategy=Strategy.Tree, precision=p, multithreading=False)
        assert s.strategy == Strategy.Tree
        assert s.precision == p
        assert s.multithreading is False

    def test_class_constants(self) -> None:
        """Test that class constants are accessible."""
        assert Solver.LIST.strategy == Strategy.List
        assert Solver.LIST.multithreading is True

        assert Solver.TREE.strategy == Strategy.Tree
        assert Solver.TREE.multithreading is True

        assert Solver.FRAG.strategy == Strategy.Frag
        assert Solver.FRAG.multithreading is True

        assert Solver.AUTO.strategy == Strategy.Auto
        assert Solver.AUTO.multithreading is True

    def test_repr(self) -> None:
        """Test repr representation."""
        s = Solver()
        r = repr(s)
        assert "Solver" in r
        assert "Auto" in r


class TestOverlayOptions:
    """Tests for OverlayOptions configuration class."""

    def test_default_construction(self) -> None:
        """Test creating OverlayOptions with default values."""
        o = OverlayOptions()
        assert o.preserve_input_collinear is False
        assert o.output_direction == ContourDirection.CounterClockwise
        assert o.preserve_output_collinear is False
        assert o.min_output_area == 0

    def test_custom_construction(self) -> None:
        """Test creating OverlayOptions with custom values."""
        o = OverlayOptions(
            preserve_input_collinear=True,
            output_direction=ContourDirection.Clockwise,
            preserve_output_collinear=True,
            min_output_area=100,
        )
        assert o.preserve_input_collinear is True
        assert o.output_direction == ContourDirection.Clockwise
        assert o.preserve_output_collinear is True
        assert o.min_output_area == 100

    def test_repr(self) -> None:
        """Test repr representation."""
        o = OverlayOptions()
        r = repr(o)
        assert "OverlayOptions" in r


class TestClipRule:
    """Tests for ClipRule configuration class."""

    def test_default_construction(self) -> None:
        """Test creating ClipRule with default values."""
        c = ClipRule()
        assert c.invert is False
        assert c.boundary_included is True

    def test_custom_construction(self) -> None:
        """Test creating ClipRule with custom values."""
        c = ClipRule(invert=True, boundary_included=False)
        assert c.invert is True
        assert c.boundary_included is False

    def test_equality(self) -> None:
        """Test ClipRule equality."""
        c1 = ClipRule(invert=True, boundary_included=False)
        c2 = ClipRule(invert=True, boundary_included=False)
        c3 = ClipRule(invert=False, boundary_included=False)
        assert c1 == c2
        assert c1 != c3

    def test_hashable(self) -> None:
        """Test that ClipRule is hashable."""
        c1 = ClipRule(invert=True, boundary_included=False)
        c2 = ClipRule(invert=True, boundary_included=False)
        rules = {c1, c2}
        assert len(rules) == 1

    def test_repr(self) -> None:
        """Test repr representation."""
        c = ClipRule(invert=True, boundary_included=False)
        assert repr(c) == "ClipRule(invert=true, boundary_included=false)"
