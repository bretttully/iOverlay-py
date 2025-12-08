//! Python wrapper for clip operations.
//!
//! Provides functions for clipping polylines against polygon shapes.

use pyo3::prelude::*;
use pyo3::types::PyAny;
use pyo3_stub_gen::derive::gen_stub_pyfunction;

use i_overlay_core::core::fill_rule::FillRule;
use i_overlay_core::core::solver::Solver;
use i_overlay_core::float::string_overlay::FloatStringOverlay;
use i_overlay_core::string::clip::ClipRule;

use crate::clip::PyClipRule;
use crate::enums::PyFillRule;
use crate::options::PySolver;
use crate::types::{extract_paths, extract_shapes, paths_to_python, Paths, Shapes};

/// Build Rust Solver from Python solver.
fn build_solver(py_solver: Option<&PySolver>) -> Solver {
    match py_solver {
        Some(s) => s.into(),
        None => Solver::default(),
    }
}

/// Clip polylines by shapes.
///
/// This function clips polylines against polygon shapes, returning only
/// the portions of the polylines that are inside (or outside, if inverted)
/// the shapes.
///
/// Args:
///     polylines: The polylines to clip as `list[list[tuple[float, float]]]`.
///     shapes: The clipping shapes as `list[list[list[tuple[float, float]]]]`.
///     fill_rule: The fill rule for determining filled regions.
///     clip_rule: The clipping rule determining inclusion/exclusion behavior.
///     solver: Optional solver configuration.
///
/// Returns:
///     Clipped polylines in the same format as input polylines.
///
/// Example:
///     ```python
///     from i_overlay import clip_by, FillRule, ClipRule
///
///     # A line passing through a square
///     polylines = [[(-1, 1), (3, 1)]]
///
///     # A square
///     shapes = [[[(0, 0), (0, 2), (2, 2), (2, 0)]]]
///
///     # Clip the line to the square (keep inside portion)
///     result = clip_by(polylines, shapes, FillRule.EvenOdd, ClipRule())
///     # Result contains the portion of the line inside the square
///     ```
#[gen_stub_pyfunction]
#[pyfunction]
#[pyo3(signature = (polylines, shapes, fill_rule, clip_rule, *, solver=None))]
pub fn clip_by(
    py: Python<'_>,
    polylines: &Bound<'_, PyAny>,
    shapes: &Bound<'_, PyAny>,
    fill_rule: PyFillRule,
    clip_rule: PyClipRule,
    solver: Option<&PySolver>,
) -> PyResult<Py<PyAny>> {
    let rust_polylines = extract_paths(polylines)?;
    let rust_shapes = extract_shapes(shapes)?;

    let result = perform_clip(
        &rust_polylines,
        &rust_shapes,
        fill_rule.into(),
        clip_rule.into(),
        solver,
    );

    paths_to_python(py, &result)
}

/// Internal function to perform clip operation.
fn perform_clip(
    polylines: &Paths,
    shapes: &Shapes,
    fill_rule: FillRule,
    clip_rule: ClipRule,
    py_solver: Option<&PySolver>,
) -> Paths {
    let solver = build_solver(py_solver);

    // Note: with_shape_and_string takes (shape, string) order
    // where shape is the clipping polygon and string is the polylines to clip
    let string_overlay = FloatStringOverlay::with_shape_and_string(shapes, polylines);

    string_overlay.clip_string_lines_with_solver(fill_rule, clip_rule, solver)
}
