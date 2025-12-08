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
