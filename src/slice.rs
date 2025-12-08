//! Python wrapper for shape slicing operations.
//!
//! Provides functions for slicing shapes using polylines.

use pyo3::prelude::*;
use pyo3::types::PyAny;
use pyo3_stub_gen::derive::gen_stub_pyfunction;

use i_overlay_core::core::fill_rule::FillRule;
use i_overlay_core::core::solver::Solver;
use i_overlay_core::float::overlay::OverlayOptions;
use i_overlay_core::float::string_overlay::FloatStringOverlay;
use i_overlay_core::string::rule::StringRule;

use crate::enums::PyFillRule;
use crate::options::{PyOverlayOptions, PySolver};
use crate::types::{extract_paths, extract_shapes, shapes_to_python, Paths, Shapes};

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

/// Build Rust Solver from Python solver.
fn build_solver(py_solver: Option<&PySolver>) -> Solver {
    match py_solver {
        Some(s) => s.into(),
        None => Solver::default(),
    }
}

/// Slice shapes using polylines.
///
/// This function cuts shapes along the specified polylines, dividing them
/// into smaller pieces.
///
/// Args:
///     shapes: The shapes to slice as `list[list[list[tuple[float, float]]]]`.
///     polylines: The cutting lines as `list[list[tuple[float, float]]]`.
///     fill_rule: The fill rule for determining filled regions.
///     options: Optional overlay options for controlling output behavior.
///     solver: Optional solver configuration.
///
/// Returns:
///     Sliced shapes in the same format as input.
///
/// Example:
///     ```python
///     from i_overlay import slice_by, FillRule
///
///     # A square
///     shapes = [[[(0, 0), (0, 2), (2, 2), (2, 0)]]]
///
///     # A horizontal line cutting through the middle
///     polylines = [[(0, 1), (2, 1)]]
///
///     # Slice the square
///     result = slice_by(shapes, polylines, FillRule.EvenOdd)
///     # Result contains two rectangles
///     ```
#[gen_stub_pyfunction]
#[pyfunction]
#[pyo3(signature = (shapes, polylines, fill_rule, *, options=None, solver=None))]
pub fn slice_by(
    py: Python<'_>,
    shapes: &Bound<'_, PyAny>,
    polylines: &Bound<'_, PyAny>,
    fill_rule: PyFillRule,
    options: Option<&PyOverlayOptions>,
    solver: Option<&PySolver>,
) -> PyResult<Py<PyAny>> {
    let rust_shapes = extract_shapes(shapes)?;
    let rust_polylines = extract_paths(polylines)?;

    let result = perform_slice(
        &rust_shapes,
        &rust_polylines,
        fill_rule.into(),
        options,
        solver,
    );

    shapes_to_python(py, &result)
}

/// Internal function to perform slice operation.
fn perform_slice(
    shapes: &Shapes,
    polylines: &Paths,
    fill_rule: FillRule,
    py_options: Option<&PyOverlayOptions>,
    py_solver: Option<&PySolver>,
) -> Shapes {
    let default_options = PyOverlayOptions::default();
    let options_ref = py_options.unwrap_or(&default_options);

    let rust_options = build_overlay_options(options_ref);
    let solver = build_solver(py_solver);

    let mut string_overlay = FloatStringOverlay::with_shape_and_string(shapes, polylines);

    match string_overlay.build_graph_view_with_solver(fill_rule, solver) {
        Some(graph) => graph.extract_shapes_custom(StringRule::Slice, rust_options),
        None => Vec::new(),
    }
}
