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
from i_overlay import FillRule, OverlayRule

# Define two overlapping rectangles
subject = [[(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]]
clip = [[(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)]]

# Coming in future phases:
# result = overlay(subject, clip, OverlayRule.Union, FillRule.NonZero)
```

## Enums

- `FillRule`: EvenOdd, NonZero, Positive, Negative
- `OverlayRule`: Subject, Clip, Intersect, Union, Difference, InverseDifference, Xor
- `ContourDirection`: CounterClockwise, Clockwise
- `ShapeType`: Subject, Clip
- `Strategy`: List, Tree, Frag, Auto
- `LineCap`: Butt, Round, Square
- `LineJoin`: Bevel, Miter, Round

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
