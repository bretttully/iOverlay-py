//! Python wrapper for outline operations.
//!
//! Provides functions for creating offset outlines from shapes.

use pyo3::prelude::*;
use pyo3::types::PyAny;
use pyo3_stub_gen::derive::gen_stub_pyfunction;

use i_overlay_core::float::overlay::OverlayOptions;
use i_overlay_core::mesh::outline::offset::OutlineOffset;

use crate::options::PyOverlayOptions;
use crate::style::PyOutlineStyle;
use crate::types::{extract_shapes, shapes_to_python, Shapes};

/// Build Rust OverlayOptions from Python options.
fn build_overlay_options(py_options: &PyOverlayOptions) -> OverlayOptions<f64> {
    OverlayOptions {
        preserve_input_collinear: py_options.preserve_input_collinear,
        output_direction: py_options.output_direction.into(),
        preserve_output_collinear: py_options.preserve_output_collinear,
        min_output_area: py_options.min_output_area as f64,
        clean_result: true,
    }
}

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
