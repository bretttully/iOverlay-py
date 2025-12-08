# iOverlay-py

Python bindings for [iOverlay](https://github.com/iShape-Rust/iOverlay) - Boolean Operations for 2D Polygons.

## Features

- **Boolean Operations**: Union, Intersection, Difference, XOR
- **Self-Intersection Resolution**: Clean up complex polygons
- **Polygon Slicing**: Cut polygons with polylines
- **Polyline Clipping**: Clip lines by polygon boundaries
- **Stroke & Outline**: Generate stroke geometry for paths

## Installation

```bash
# From conda-forge (recommended)
conda install -c conda-forge i_overlay

# From source
pip install .
```

## Quick Start

```python
from i_overlay import FillRule, OverlayRule, overlay

# Define two overlapping rectangles as shapes
# Each shape is a list of contours (first is exterior, rest are holes)
subject = [[[(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]]]
clip = [[[(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)]]]

# Perform Boolean union
result = overlay(subject, clip, OverlayRule.Union, FillRule.NonZero)
print(f"Union result: {len(result)} shape(s)")

# Perform Boolean intersection
result = overlay(subject, clip, OverlayRule.Intersect, FillRule.NonZero)
print(f"Intersection result: {len(result)} shape(s)")
```

### Using FloatOverlayGraph for Multiple Operations

When you need to perform multiple Boolean operations on the same geometry,
use `FloatOverlayGraph` for better efficiency:

```python
from i_overlay import FillRule, OverlayRule, FloatOverlayGraph

subject = [[[(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]]]
clip = [[[(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)]]]

# Build graph once
graph = FloatOverlayGraph(subject, clip, FillRule.NonZero)

# Extract multiple results efficiently
union = graph.extract_shapes(OverlayRule.Union)
intersection = graph.extract_shapes(OverlayRule.Intersect)
difference = graph.extract_shapes(OverlayRule.Difference)
xor = graph.extract_shapes(OverlayRule.Xor)
```

## Enums

- `FillRule`: EvenOdd, NonZero, Positive, Negative
- `OverlayRule`: Subject, Clip, Intersect, Union, Difference, InverseDifference, Xor
- `ContourDirection`: CounterClockwise, Clockwise
- `ShapeType`: Subject, Clip
- `Strategy`: List, Tree, Frag, Auto
- `LineCap`: Butt, Round, Square
- `LineJoin`: Bevel, Miter, Round

## Configuration Classes

- `OverlayOptions`: Control output behavior (direction, collinear preservation, min area)
- `Solver`: Algorithm selection and precision settings
- `Precision`: Numerical precision configuration
- `ClipRule`: Clipping behavior (invert, boundary inclusion)
- `StrokeStyle`: Stroke width, line caps, and joins
- `OutlineStyle`: Offset distances and joins

## More Examples

### Simplify Self-Intersecting Shapes

```python
from i_overlay import simplify_shape, FillRule

# A figure-8 shape (self-intersecting)
figure_eight = [[[(0, 0), (2, 2), (2, 0), (0, 2)]]]

# Simplify to resolve self-intersection
result = simplify_shape(figure_eight, FillRule.EvenOdd)
# Result: two separate triangles
```

### Slice Shapes with Polylines

```python
from i_overlay import slice_by, FillRule

# A square
shapes = [[[(0, 0), (2, 0), (2, 2), (0, 2)]]]

# A horizontal cutting line
polylines = [[(0, 1), (2, 1)]]

# Slice the square into two rectangles
result = slice_by(shapes, polylines, FillRule.EvenOdd)
```

### Clip Polylines by Shapes

```python
from i_overlay import clip_by, FillRule, ClipRule

# A line passing through a square
polylines = [[(-1, 1), (3, 1)]]
shapes = [[[(0, 0), (2, 0), (2, 2), (0, 2)]]]

# Keep only the portion inside the square
result = clip_by(polylines, shapes, FillRule.EvenOdd, ClipRule())

# Or keep portions outside (invert)
result = clip_by(polylines, shapes, FillRule.EvenOdd, ClipRule(invert=True))
```

### Create Stroked Paths

```python
from i_overlay import stroke, StrokeStyle, LineCap, LineJoin

# An open path
paths = [[(0, 0), (10, 0), (10, 10)]]

# Create a stroke with width 2 and round caps
style = StrokeStyle(2.0, start_cap=LineCap.Round, end_cap=LineCap.Round)
result = stroke(paths, style)

# For closed paths, set is_closed=True
closed_paths = [[(0, 0), (10, 0), (10, 10), (0, 10)]]
result = stroke(closed_paths, style, is_closed=True)

# Custom caps - define your own cap shape with points
# Points are relative to stroke width (-0.5 to 0.5 perpendicular)
arrow_cap = [(0, -0.5), (1, 0), (0, 0.5)]  # Arrow pointing forward
style = StrokeStyle(2.0, end_cap_points=arrow_cap)
result = stroke(paths, style)
```

### Create Offset Outlines

```python
from i_overlay import outline, OutlineStyle, LineJoin

# A square shape (counter-clockwise for outer boundary)
shapes = [[[(0, 0), (10, 0), (10, 10), (0, 10)]]]

# Expand/contract the shape boundary
style = OutlineStyle(1.0, join=LineJoin.Round)
result = outline(shapes, style)

# Use different inner and outer offsets
style = OutlineStyle(offset=1.0, outer_offset=2.0, inner_offset=0.5)
result = outline(shapes, style)
```

## Development

```bash
# Build for development
maturin develop

# Run tests
pytest tests/

# Generate stubs
cargo run --bin stub_gen
```

## License

MIT License - see LICENSE file for details.
