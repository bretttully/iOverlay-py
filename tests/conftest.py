"""Pytest configuration and fixtures for i_overlay tests."""

import pytest


@pytest.fixture
def simple_rectangle() -> list[list[tuple[float, float]]]:
    """A simple unit rectangle from (0,0) to (1,1)."""
    return [[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]]


@pytest.fixture
def offset_rectangle() -> list[list[tuple[float, float]]]:
    """A rectangle from (0.5,0.5) to (1.5,1.5)."""
    return [[(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5)]]
