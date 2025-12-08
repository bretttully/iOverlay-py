//! Python wrapper for outline operations.
//!
//! Provides functions for creating offset outlines from shapes.

use pyo3::prelude::*;
use pyo3::types::PyAny;
use pyo3_stub_gen::derive::gen_stub_pyfunction;

use i_overlay_core::mesh::outline::offset::OutlineOffset;

use crate::options::{build_overlay_options, PyOverlayOptions};
use crate::style::PyOutlineStyle;
use crate::types::{extract_shapes, shapes_to_python, Shapes};

/// Create offset outline shapes from shapes.
///
/// Offsets the boundary of shapes inward and/or outward to create
/// thickened outlines.
///
/// Args:
///     shapes: The shapes to outline as `list[list[list[tuple[float, float]]]]`.
///     style: The outline style configuration.
///     options: Optional overlay options for controlling output behavior.
///
/// Returns:
///     Outlined shapes as `list[list[list[tuple[float, float]]]]`.
///     Returns an empty list if the input shapes are empty.
///
/// Example:
///     ```python
///     from i_overlay import outline, OutlineStyle, LineJoin
///
///     # A square shape
///     shapes = [[[(0, 0), (10, 0), (10, 10), (0, 10)]]]
///
///     # Create an outline with offset 1
///     style = OutlineStyle(1.0, join=LineJoin.Round)
///     result = outline(shapes, style)
///     ```
#[gen_stub_pyfunction]
#[pyfunction]
#[pyo3(signature = (shapes, style, *, options=None))]
pub fn outline(
    py: Python<'_>,
    shapes: &Bound<'_, PyAny>,
    style: &PyOutlineStyle,
    options: Option<&PyOverlayOptions>,
) -> PyResult<Py<PyAny>> {
    let rust_shapes = extract_shapes(shapes)?;

    let result = perform_outline(&rust_shapes, style, options);

    shapes_to_python(py, &result)
}

/// Internal function to perform outline operation.
fn perform_outline(
    shapes: &Shapes,
    py_style: &PyOutlineStyle,
    py_options: Option<&PyOverlayOptions>,
) -> Shapes {
    if shapes.is_empty() {
        return Vec::new();
    }

    let rust_style = py_style.to_rust_style();

    match py_options {
        Some(opts) => {
            let rust_options = build_overlay_options(opts);
            shapes.outline_custom(&rust_style, rust_options)
        }
        None => shapes.outline(&rust_style),
    }
}
