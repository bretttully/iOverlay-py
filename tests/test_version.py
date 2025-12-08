"""Tests for version information."""

import i_overlay


def test_version_exists() -> None:
    """Test that __version__ attribute exists."""
    assert hasattr(i_overlay, "__version__")


def test_version_is_string() -> None:
    """Test that __version__ is a string."""
    assert isinstance(i_overlay.__version__, str)


def test_version_format() -> None:
    """Test that __version__ follows semver format."""
    version = i_overlay.__version__
    parts = version.split(".")
    assert len(parts) >= 2, f"Version '{version}' should have at least major.minor"
    # First two parts should be numeric
    assert parts[0].isdigit(), f"Major version '{parts[0]}' should be numeric"
    assert parts[1].isdigit(), f"Minor version '{parts[1]}' should be numeric"
