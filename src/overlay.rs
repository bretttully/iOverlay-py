//! Python wrapper for Boolean overlay operations.
//!
//! Provides functions for performing Boolean operations (union, intersection,
//! difference, XOR) on 2D polygons.

use pyo3::prelude::*;
use pyo3::types::PyAny;
use pyo3_stub_gen::derive::gen_stub_pyfunction;

use i_overlay_core::core::fill_rule::FillRule;
use i_overlay_core::core::overlay_rule::OverlayRule;
use i_overlay_core::core::solver::Solver;
use i_overlay_core::float::overlay::{FloatOverlay, OverlayOptions};

use crate::enums::{PyFillRule, PyOverlayRule};
use crate::options::{PyOverlayOptions, PySolver};
use crate::types::{extract_shapes, shapes_to_python, Shapes};

/// Perform a Boolean operation on two sets of shapes.
///
/// Args:
///     subject: The subject shapes as `list[list[list[tuple[float, float]]]]`.
///         Each shape is a list of contours, where the first contour is the
///         outer boundary and subsequent contours are holes.
///     clip: The clip shapes in the same format as subject.
///     overlay_rule: The Boolean operation to perform (Union, Intersect, Difference, etc.)
///     fill_rule: The fill rule to determine filled regions (EvenOdd, NonZero, etc.)
///     options: Optional overlay options for controlling output behavior.
///     solver: Optional solver configuration for algorithm selection and precision.
///
/// Returns:
///     Result shapes in the same format as input: `list[list[list[tuple[float, float]]]]`
///
/// Example:
///     ```python
///     from i_overlay import overlay, OverlayRule, FillRule
///
///     # Two overlapping rectangles
///     subject = [[[(0, 0), (0, 2), (2, 2), (2, 0)]]]  # 2x2 square at origin
///     clip = [[[(1, 1), (1, 3), (3, 3), (3, 1)]]]     # 2x2 square offset by (1,1)
///
///     # Union - combine both shapes
///     result = overlay(subject, clip, OverlayRule.Union, FillRule.EvenOdd)
///
///     # Intersection - find overlapping area
///     result = overlay(subject, clip, OverlayRule.Intersect, FillRule.EvenOdd)
///     ```
#[gen_stub_pyfunction]
#[pyfunction]
#[pyo3(signature = (subject, clip, overlay_rule, fill_rule, *, options=None, solver=None))]
pub fn overlay(
    py: Python<'_>,
    subject: &Bound<'_, PyAny>,
    clip: &Bound<'_, PyAny>,
    overlay_rule: PyOverlayRule,
    fill_rule: PyFillRule,
    options: Option<&PyOverlayOptions>,
    solver: Option<&PySolver>,
) -> PyResult<Py<PyAny>> {
    // Extract shapes from Python
    let subj_shapes = extract_shapes(subject)?;
    let clip_shapes = extract_shapes(clip)?;

    // Perform the overlay operation
    let result = perform_overlay(
        &subj_shapes,
        &clip_shapes,
        overlay_rule.into(),
        fill_rule.into(),
        options,
        solver,
    );

    // Convert result to Python
    shapes_to_python(py, &result)
}

/// Internal function to perform overlay operation.
fn perform_overlay(
    subject: &Shapes,
    clip: &Shapes,
    overlay_rule: OverlayRule,
    fill_rule: FillRule,
    py_options: Option<&PyOverlayOptions>,
    py_solver: Option<&PySolver>,
) -> Shapes {
    let default_options = PyOverlayOptions::default();
    let options_ref = py_options.unwrap_or(&default_options);

    // Build the Rust overlay options
    let rust_options: OverlayOptions<f64> = OverlayOptions {
        preserve_input_collinear: options_ref.preserve_input_collinear,
        output_direction: options_ref.output_direction.into(),
        preserve_output_collinear: options_ref.preserve_output_collinear,
        min_output_area: options_ref.min_output_area as f64,
        clean_result: true,
    };

    // Build the solver
    let solver: Solver = match py_solver {
        Some(s) => s.into(),
        None => Solver::default(),
    };

    // Create the overlay and perform the operation
    let mut float_overlay =
        FloatOverlay::with_subj_and_clip_custom(subject, clip, rust_options, solver);

    float_overlay.overlay(overlay_rule, fill_rule)
}
