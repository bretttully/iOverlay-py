//! Python bindings for iOverlay
//!
//! This module provides Python classes and functions for performing boolean operations
//! on 2D polygons including union, intersection, difference, and XOR operations.

use pyo3::prelude::*;
use pyo3_stub_gen::define_stub_info_gatherer;

mod enums;

pub use enums::PyContourDirection;
pub use enums::PyFillRule;
pub use enums::PyLineCap;
pub use enums::PyLineJoin;
pub use enums::PyOverlayRule;
pub use enums::PyShapeType;
pub use enums::PyStrategy;

/// i_overlay - Python bindings for iOverlay boolean operations on 2D polygons
///
/// This library provides efficient boolean operations for 2D polygons including:
/// - Union: Combine multiple shapes into one
/// - Intersection: Find common area between shapes
/// - Difference: Subtract one shape from another
/// - XOR: Find areas unique to each shape
///
/// Enums:
///     FillRule: Determines how shapes are filled (EvenOdd, NonZero, Positive, Negative)
///     OverlayRule: Boolean operation type (Subject, Clip, Intersect, Union, Difference, InverseDifference, Xor)
///     ContourDirection: Winding direction (CounterClockwise, Clockwise)
///     ShapeType: Shape classification (Subject, Clip)
///     Strategy: Algorithm selection (List, Tree, Frag, Auto)
///     LineCap: Line endpoint style (Butt, Round, Square)
///     LineJoin: Line corner style (Bevel, Miter, Round)
#[pymodule]
fn i_overlay(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Register enums
    m.add_class::<PyFillRule>()?;
    m.add_class::<PyOverlayRule>()?;
    m.add_class::<PyContourDirection>()?;
    m.add_class::<PyShapeType>()?;
    m.add_class::<PyStrategy>()?;
    m.add_class::<PyLineCap>()?;
    m.add_class::<PyLineJoin>()?;

    // Add version
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;

    Ok(())
}

// Define stub info gatherer for generating .pyi files
define_stub_info_gatherer!(stub_info);
