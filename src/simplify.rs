//! Python wrapper for shape simplification.
//!
//! Provides functions for simplifying shapes by resolving self-intersections.

use pyo3::prelude::*;
use pyo3::types::PyAny;
use pyo3_stub_gen::derive::gen_stub_pyfunction;

use i_overlay_core::core::fill_rule::FillRule;
use i_overlay_core::core::overlay_rule::OverlayRule;
use i_overlay_core::core::solver::Solver;
use i_overlay_core::float::overlay::FloatOverlay;

use crate::enums::PyFillRule;
use crate::options::{build_overlay_options, PyOverlayOptions, PySolver};
use crate::types::{extract_shapes, shapes_to_python, Shapes};

/// Build Rust Solver from Python solver.
fn build_solver(py_solver: Option<&PySolver>) -> Solver {
    match py_solver {
        Some(s) => s.into(),
        None => Solver::default(),
    }
}

/// Simplify shapes by resolving self-intersections.
///
/// This function cleans up shapes by removing self-intersections and
/// normalizing the geometry according to the specified fill rule.
///
/// Args:
///     shapes: The shapes to simplify as `list[list[list[tuple[float, float]]]]`.
///     fill_rule: The fill rule for determining filled regions.
///     options: Optional overlay options for controlling output behavior.
///     solver: Optional solver configuration.
///
/// Returns:
///     Simplified shapes in the same format as input.
///
/// Example:
///     ```python
///     from i_overlay import simplify_shape, FillRule
///
///     # A figure-8 shape (self-intersecting)
///     shape = [[[(0, 0), (2, 2), (2, 0), (0, 2)]]]
///
///     # Simplify to resolve self-intersection
///     result = simplify_shape(shape, FillRule.EvenOdd)
///     ```
#[gen_stub_pyfunction]
#[pyfunction]
#[pyo3(signature = (shapes, fill_rule, *, options=None, solver=None))]
pub fn simplify_shape(
    py: Python<'_>,
    shapes: &Bound<'_, PyAny>,
    fill_rule: PyFillRule,
    options: Option<&PyOverlayOptions>,
    solver: Option<&PySolver>,
) -> PyResult<Py<PyAny>> {
    let rust_shapes = extract_shapes(shapes)?;

    let result = perform_simplify(&rust_shapes, fill_rule.into(), options, solver);

    shapes_to_python(py, &result)
}

/// Internal function to perform simplification.
fn perform_simplify(
    shapes: &Shapes,
    fill_rule: FillRule,
    py_options: Option<&PyOverlayOptions>,
    py_solver: Option<&PySolver>,
) -> Shapes {
    let default_options = PyOverlayOptions::default();
    let options_ref = py_options.unwrap_or(&default_options);

    let rust_options = build_overlay_options(options_ref);
    let solver = build_solver(py_solver);

    // Empty clip for subject-only operation
    let empty_clip: Shapes = Vec::new();

    let mut float_overlay =
        FloatOverlay::with_subj_and_clip_custom(shapes, &empty_clip, rust_options, solver);

    // Use Subject rule to just process the subject shapes
    float_overlay.overlay(OverlayRule::Subject, fill_rule)
}
