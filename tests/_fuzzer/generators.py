"""Random polygon generators for fuzzing i_overlay.

This module provides generators that create random polygon geometries
for testing boolean operations. Each generator produces pairs of
subject and clip shapes that can be used with overlay operations.
"""

from __future__ import annotations

import abc
import dataclasses
from typing import TYPE_CHECKING

import numpy as np
import shapely
import shapely.geometry

if TYPE_CHECKING:
    from numpy.random import Generator as RngGenerator

# Type aliases matching i_overlay
Point = tuple[float, float]
Contour = list[Point]
Shape = list[Contour]
Shapes = list[Shape]

type GenericPoly = shapely.geometry.Polygon | shapely.geometry.MultiPolygon


def shapely_to_shapes(geom: GenericPoly) -> Shapes:
    """Convert a shapely geometry to i_overlay Shapes format."""
    if geom.is_empty:
        return []

    if isinstance(geom, shapely.geometry.Polygon):
        polys = [geom]
    elif isinstance(geom, shapely.geometry.MultiPolygon):
        polys = list(geom.geoms)
    else:
        return []

    shapes: Shapes = []
    for poly in polys:
        if poly.is_empty:
            continue
        shape: Shape = []
        # Exterior ring
        shape.append(list(poly.exterior.coords[:-1]))  # Remove closing point
        # Interior rings (holes)
        for interior in poly.interiors:
            shape.append(list(interior.coords[:-1]))
        shapes.append(shape)

    return shapes


def clip_to_unit_square(poly: GenericPoly) -> GenericPoly:
    """Clip geometry to the unit square [0,1] x [0,1]."""
    bbox = shapely.geometry.box(0, 0, 1, 1)
    return poly.intersection(bbox)


def scale_geometry(poly: GenericPoly, factor: float) -> GenericPoly:
    """Scale geometry by a factor around the origin."""
    return shapely.transform(poly, lambda pts: pts * factor)


def translate_geometry(poly: GenericPoly, xoff: float, yoff: float) -> GenericPoly:
    """Translate geometry by offset."""
    return shapely.transform(poly, lambda pts: pts + np.array([xoff, yoff]))


@dataclasses.dataclass(frozen=True)
class RandomPolyGenerator(abc.ABC):
    """Abstract base class for random polygon generators.

    Subclasses implement _fill_unit_square to create geometries within
    the unit square [0,1] x [0,1]. The __call__ method then scales and
    converts to i_overlay format.
    """

    # Scale factor to apply to unit square geometries
    scale_factor: float = 50.0

    @classmethod
    @abc.abstractmethod
    def name(cls) -> str:
        """Get the name of this generator."""

    def __call__(self, seed: int) -> Shapes:
        """Generate random shapes for the given seed.

        Args:
            seed: Random seed for reproducibility.

        Returns:
            List of shapes in i_overlay format.
        """
        rng = np.random.default_rng(seed)
        poly = self._fill_unit_square(rng)

        if not poly.is_valid:
            # Try to make it valid
            poly = shapely.make_valid(poly)

        # Clip to unit square and scale
        poly = clip_to_unit_square(poly)
        poly = scale_geometry(poly, self.scale_factor)

        return shapely_to_shapes(poly)

    @abc.abstractmethod
    def _fill_unit_square(self, rng: RngGenerator) -> GenericPoly:
        """Fill the unit square with random polygons.

        Args:
            rng: NumPy random generator.

        Returns:
            A shapely Polygon or MultiPolygon within [0,1] x [0,1].
        """


@dataclasses.dataclass(frozen=True)
class RandomSpotsGenerator(RandomPolyGenerator):
    """Generates random circular spot geometries.

    Creates multiple overlapping circular spots with randomized radii
    and centers distributed across the unit square.
    """

    vertices_per_spot: int = 20
    mean_radius: float = 0.08
    n_spots: int = 25

    @classmethod
    def name(cls) -> str:
        return "spots"

    def _fill_unit_square(self, rng: RngGenerator) -> GenericPoly:
        polygons = []
        centers = rng.uniform(0, 1, size=(self.n_spots, 2))
        radii = rng.normal(self.mean_radius, 0.3 * self.mean_radius, size=self.n_spots)
        radii = np.clip(radii, 0.01, 0.3)  # Ensure reasonable radii

        for radius, (cx, cy) in zip(radii, centers, strict=True):
            poly = self._make_spot(rng, radius, cx, cy)
            if poly is not None and poly.is_valid and not poly.is_empty:
                polygons.append(poly)

        if not polygons:
            # Fallback to a simple square
            return shapely.geometry.box(0.25, 0.25, 0.75, 0.75)

        return shapely.union_all(polygons)

    def _make_spot(self, rng: RngGenerator, radius: float, cx: float, cy: float) -> GenericPoly | None:
        """Create a slightly irregular circular spot."""
        theta = np.linspace(0, 2 * np.pi, num=self.vertices_per_spot, endpoint=False)
        # Add some randomness to the radius
        radii = radius * (1 + rng.uniform(-0.2, 0.2, size=self.vertices_per_spot))
        x = cx + radii * np.cos(theta)
        y = cy + radii * np.sin(theta)
        coords = list(zip(x, y, strict=True))

        try:
            poly = shapely.geometry.Polygon(coords)
            if poly.is_valid:
                return poly
            return shapely.make_valid(poly)
        except Exception:
            return None


@dataclasses.dataclass(frozen=True)
class RandomCenterTargetsGenerator(RandomPolyGenerator):
    """Generates concentric ring patterns around a random center.

    Creates target-like patterns with consistent arc lengths,
    producing nested rings that may overlap with other shapes.
    """

    min_arc_length: float = 0.02
    radius_step: float = 0.03
    ring_width: float = 0.02

    @classmethod
    def name(cls) -> str:
        return "center_targets"

    def _fill_unit_square(self, rng: RngGenerator) -> GenericPoly:
        polygons = []
        cx, cy = 0.5 + rng.uniform(-0.2, 0.2, size=2)

        radius = 0.45
        while radius > 2 * self.radius_step:
            ring = self._make_ring(radius, cx, cy)
            if ring is not None and ring.is_valid and not ring.is_empty:
                polygons.append(ring)
            radius -= self.radius_step * 1.5

        if not polygons:
            return shapely.geometry.box(0.25, 0.25, 0.75, 0.75)

        return shapely.union_all(polygons)

    def _make_ring(self, radius: float, cx: float, cy: float) -> GenericPoly | None:
        """Create a ring at the given radius."""
        outer = self._make_circle(radius, cx, cy)
        inner_radius = radius - self.ring_width
        if inner_radius <= 0:
            return outer
        inner = self._make_circle(inner_radius, cx, cy)

        try:
            ring = outer.difference(inner)
            if ring.is_valid:
                return ring
            return shapely.make_valid(ring)
        except Exception:
            return outer

    def _make_circle(self, radius: float, cx: float, cy: float) -> GenericPoly:
        """Create a circle with vertices based on arc length."""
        delta_theta = self.min_arc_length / max(radius, 0.01)
        n_steps = max(8, int(np.round(2 * np.pi / delta_theta)))
        theta = np.linspace(0, 2 * np.pi, num=n_steps, endpoint=False)
        x = cx + radius * np.cos(theta)
        y = cy + radius * np.sin(theta)
        return shapely.geometry.Polygon(zip(x, y, strict=True))


@dataclasses.dataclass(frozen=True)
class RandomRadiusTargetsGenerator(RandomPolyGenerator):
    """Generates concentric rings with randomly perturbed radii.

    Creates varied, non-uniform circular patterns where each ring
    has slight random variations in its radius.
    """

    min_arc_length: float = 0.02
    radius_step: float = 0.04
    ring_width: float = 0.025
    radius_noise: float = 0.01

    @classmethod
    def name(cls) -> str:
        return "radius_targets"

    def _fill_unit_square(self, rng: RngGenerator) -> GenericPoly:
        polygons = []
        radius = 0.45

        while radius > 2 * self.radius_step:
            ring = self._make_ring(rng, radius)
            if ring is not None and ring.is_valid and not ring.is_empty:
                polygons.append(ring)
            radius -= self.radius_step * 1.5

        if not polygons:
            return shapely.geometry.box(0.25, 0.25, 0.75, 0.75)

        return shapely.union_all(polygons)

    def _make_ring(self, rng: RngGenerator, radius: float) -> GenericPoly | None:
        """Create a ring with randomized radius."""
        outer = self._make_circle(rng, radius)
        inner_radius = radius - self.ring_width
        if inner_radius <= 0:
            return outer
        inner = self._make_circle(rng, inner_radius)

        try:
            ring = outer.difference(inner)
            if ring.is_valid:
                return ring
            return shapely.make_valid(ring)
        except Exception:
            return outer

    def _make_circle(self, rng: RngGenerator, radius: float) -> GenericPoly:
        """Create a circle with random radius perturbations."""
        delta_theta = self.min_arc_length / max(radius, 0.01)
        n_steps = max(8, int(np.round(2 * np.pi / delta_theta)))
        theta = np.linspace(0, 2 * np.pi, num=n_steps, endpoint=False)
        # Add noise to radius
        radii = radius + rng.uniform(-self.radius_noise, self.radius_noise, size=n_steps)
        x = 0.5 + radii * np.cos(theta)
        y = 0.5 + radii * np.sin(theta)
        return shapely.geometry.Polygon(zip(x, y, strict=True))


@dataclasses.dataclass(frozen=True)
class RandomPolygonsGenerator(RandomPolyGenerator):
    """Generates random simple polygons.

    Creates polygons by generating random points and computing
    their convex hull or alpha shape.
    """

    n_polygons: int = 10
    min_vertices: int = 4
    max_vertices: int = 12

    @classmethod
    def name(cls) -> str:
        return "random_polygons"

    def _fill_unit_square(self, rng: RngGenerator) -> GenericPoly:
        polygons = []

        for _ in range(self.n_polygons):
            poly = self._make_random_polygon(rng)
            if poly is not None and poly.is_valid and not poly.is_empty:
                polygons.append(poly)

        if not polygons:
            return shapely.geometry.box(0.25, 0.25, 0.75, 0.75)

        return shapely.union_all(polygons)

    def _make_random_polygon(self, rng: RngGenerator) -> GenericPoly | None:
        """Create a random polygon using convex hull of random points."""
        n_vertices = rng.integers(self.min_vertices, self.max_vertices + 1)

        # Generate random center and size
        cx, cy = rng.uniform(0.1, 0.9, size=2)
        size = rng.uniform(0.05, 0.25)

        # Generate points in a roughly circular distribution
        angles = np.sort(rng.uniform(0, 2 * np.pi, size=n_vertices))
        radii = size * (0.5 + 0.5 * rng.uniform(0, 1, size=n_vertices))

        x = cx + radii * np.cos(angles)
        y = cy + radii * np.sin(angles)
        coords = list(zip(x, y, strict=True))

        try:
            poly = shapely.geometry.Polygon(coords)
            if poly.is_valid:
                return poly
            return shapely.make_valid(poly)
        except Exception:
            return None
