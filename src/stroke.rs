//! Python wrapper for stroke operations.
//!
//! Provides functions for creating stroked shapes from paths.

use pyo3::prelude::*;
use pyo3::types::PyAny;
use pyo3_stub_gen::derive::gen_stub_pyfunction;

use i_overlay_core::float::overlay::OverlayOptions;
use i_overlay_core::mesh::stroke::offset::StrokeOffset;

use crate::options::PyOverlayOptions;
use crate::style::PyStrokeStyle;
use crate::types::{extract_paths, shapes_to_python, Paths, Shapes};

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

/// Create stroked shapes from paths.
///
/// Converts paths into stroked shapes with the specified width, cap styles,
/// and join styles.
///
/// Args:
///     paths: The paths to stroke as `list[list[tuple[float, float]]]`.
///     style: The stroke style configuration.
///     is_closed: Whether the paths are closed (default: False).
///     options: Optional overlay options for controlling output behavior.
///
/// Returns:
///     Stroked shapes as `list[list[list[tuple[float, float]]]]`.
///
/// Example:
///     ```python
///     from i_overlay import stroke, StrokeStyle, LineCap, LineJoin
///
///     # An open path
///     paths = [[(0, 0), (10, 0), (10, 10)]]
///
///     # Create a stroke with width 2 and round caps
///     style = StrokeStyle(2.0, start_cap=LineCap.Round, end_cap=LineCap.Round)
///     result = stroke(paths, style)
///     ```
#[gen_stub_pyfunction]
#[pyfunction]
#[pyo3(signature = (paths, style, *, is_closed=false, options=None))]
pub fn stroke(
    py: Python<'_>,
    paths: &Bound<'_, PyAny>,
    style: &PyStrokeStyle,
    is_closed: bool,
    options: Option<&PyOverlayOptions>,
) -> PyResult<Py<PyAny>> {
    let rust_paths = extract_paths(paths)?;

    let result = perform_stroke(&rust_paths, style, is_closed, options);

    shapes_to_python(py, &result)
}

/// Internal function to perform stroke operation.
fn perform_stroke(
    paths: &Paths,
    py_style: &PyStrokeStyle,
    is_closed: bool,
    py_options: Option<&PyOverlayOptions>,
) -> Shapes {
    if paths.is_empty() {
        return Vec::new();
    }

    let rust_style = py_style.to_rust_style();

    match py_options {
        Some(opts) => {
            let rust_options = build_overlay_options(opts);
            paths.stroke_custom(rust_style, is_closed, rust_options)
        }
        None => paths.stroke(rust_style, is_closed),
    }
}
