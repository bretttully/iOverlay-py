"""Utilities for converting between Shapely and i_overlay types."""

from shapely import MultiPolygon, Polygon
from shapely import Point as ShapelyPoint
from shapely import box as shapely_box
from shapely.geometry.base import BaseGeometry

# Type aliases matching i_overlay format
type Point = tuple[float, float]
type Contour = list[Point]
type Shape = list[Contour]
type Shapes = list[Shape]


def polygon_to_shape(polygon: Polygon) -> Shape:
    """Convert a Shapely Polygon to i_overlay shape format.

    Args:
        polygon: A Shapely Polygon (may have holes).

    Returns:
        A shape as list of contours. First contour is the exterior boundary,
        subsequent contours are holes.
    """
    if polygon.is_empty:
        return []

    # Exterior ring - Shapely returns coords as (x, y) tuples
    # Note: Shapely closes polygons by repeating the first point, but
    # i_overlay doesn't require this (it treats paths as implicitly closed).
    # We exclude the last point which is a repeat of the first.
    exterior_coords = list(polygon.exterior.coords)[:-1]
    shape: Shape = [[(x, y) for x, y in exterior_coords]]

    # Interior rings (holes)
    for interior in polygon.interiors:
        hole_coords = list(interior.coords)[:-1]
        shape.append([(x, y) for x, y in hole_coords])

    return shape


def geometry_to_shapes(geom: BaseGeometry) -> Shapes:
    """Convert a Shapely geometry to i_overlay shapes format.

    Args:
        geom: A Shapely geometry (Polygon or MultiPolygon).

    Returns:
        Shapes as list[list[list[tuple[float, float]]]].
    """
    if geom.is_empty:
        return []

    if isinstance(geom, Polygon):
        shape = polygon_to_shape(geom)
        return [shape] if shape else []

    if isinstance(geom, MultiPolygon):
        shapes = []
        for polygon in geom.geoms:
            shape = polygon_to_shape(polygon)
            if shape:
                shapes.append(shape)
        return shapes

    msg = f"Unsupported geometry type: {type(geom)}"
    raise TypeError(msg)


def shapes_to_multipolygon(shapes: Shapes) -> MultiPolygon:
    """Convert i_overlay shapes to a Shapely MultiPolygon.

    Args:
        shapes: Shapes in i_overlay format.

    Returns:
        A Shapely MultiPolygon.
    """
    polygons = []
    for shape in shapes:
        if not shape:
            continue
        exterior = shape[0]
        holes = shape[1:] if len(shape) > 1 else None
        polygon = Polygon(exterior, holes)
        if polygon.is_valid and not polygon.is_empty:
            polygons.append(polygon)

    return MultiPolygon(polygons)


def box(minx: float, miny: float, maxx: float, maxy: float) -> Shapes:
    """Create a rectangular box as i_overlay shapes.

    Args:
        minx: Minimum x coordinate.
        miny: Minimum y coordinate.
        maxx: Maximum x coordinate.
        maxy: Maximum y coordinate.

    Returns:
        Shapes containing a single rectangular shape.
    """
    return geometry_to_shapes(shapely_box(minx, miny, maxx, maxy))


def circle(x: float, y: float, radius: float, resolution: int = 32) -> Shapes:
    """Create a circular shape as i_overlay shapes.

    Args:
        x: Center x coordinate.
        y: Center y coordinate.
        radius: Circle radius.
        resolution: Number of segments in the circle approximation.

    Returns:
        Shapes containing a single circular shape.
    """
    point = ShapelyPoint(x, y)
    circle_poly = point.buffer(radius, resolution)
    return geometry_to_shapes(circle_poly)


def polygon_with_hole(outer: list[Point], hole: list[Point]) -> Shapes:
    """Create a polygon with a hole as i_overlay shapes.

    Args:
        outer: Exterior boundary points.
        hole: Interior hole points.

    Returns:
        Shapes containing a single shape with a hole.
    """
    polygon = Polygon(outer, [hole])
    return geometry_to_shapes(polygon)
