//! Python wrapper for Boolean overlay operations.
//!
//! Provides functions and classes for performing Boolean operations (union, intersection,
//! difference, XOR) on 2D polygons.

use pyo3::prelude::*;
use pyo3::types::PyAny;
use pyo3_stub_gen::derive::{gen_stub_pyclass, gen_stub_pyfunction, gen_stub_pymethods};

use i_overlay_core::core::extract::BooleanExtractionBuffer;
use i_overlay_core::core::fill_rule::FillRule;
use i_overlay_core::core::overlay_rule::OverlayRule;
use i_overlay_core::core::solver::Solver;
use i_overlay_core::float::overlay::{FloatOverlay, OverlayOptions};

use crate::enums::{PyFillRule, PyOverlayRule};
use crate::options::{PyOverlayOptions, PySolver};
use crate::types::{extract_shapes, shapes_to_python, Shapes};

// =============================================================================
// Helper functions for building Rust types from Python types
// =============================================================================

/// Convert Python options to Rust OverlayOptions.
/// Centralizes the conversion logic for maintainability.
fn build_overlay_options(py_options: &PyOverlayOptions) -> OverlayOptions<f64> {
    OverlayOptions {
        preserve_input_collinear: py_options.preserve_input_collinear,
        output_direction: py_options.output_direction.into(),
        preserve_output_collinear: py_options.preserve_output_collinear,
        min_output_area: py_options.min_output_area as f64,
        clean_result: true,
    }
}

/// Convert optional Python solver to Rust Solver.
fn build_solver(py_solver: Option<&PySolver>) -> Solver {
    match py_solver {
        Some(s) => s.into(),
        None => Solver::default(),
    }
}

/// Create a FloatOverlay with the given shapes and configuration.
fn create_float_overlay(
    subject: &Shapes,
    clip: &Shapes,
    options: OverlayOptions<f64>,
    solver: Solver,
) -> FloatOverlay<[f64; 2], f64> {
    FloatOverlay::with_subj_and_clip_custom(subject, clip, options, solver)
}

/// Perform a Boolean operation on two sets of shapes.
///
/// This is a convenience function for one-off operations. For multiple operations
/// on the same geometry, use the `Overlay` class instead.
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

    let rust_options = build_overlay_options(options_ref);
    let solver = build_solver(py_solver);

    let mut float_overlay = create_float_overlay(subject, clip, rust_options, solver);
    float_overlay.overlay(overlay_rule, fill_rule)
}

/// An overlay graph for extracting multiple Boolean operation results from the same geometry.
///
/// This is useful when you need to perform multiple different Boolean operations
/// on the same subject and clip shapes. Building the graph once and extracting
/// multiple results is more efficient than calling `overlay()` multiple times.
///
/// Example:
///     ```python
///     from i_overlay import FloatOverlayGraph, OverlayRule, FillRule
///
///     subject = [[[(0, 0), (0, 2), (2, 2), (2, 0)]]]
///     clip = [[[(1, 1), (1, 3), (3, 3), (3, 1)]]]
///
///     # Build graph once
///     graph = FloatOverlayGraph(subject, clip, FillRule.EvenOdd)
///
///     # Extract multiple results efficiently
///     union = graph.extract_shapes(OverlayRule.Union)
///     intersection = graph.extract_shapes(OverlayRule.Intersect)
///     difference = graph.extract_shapes(OverlayRule.Difference)
///     ```
#[gen_stub_pyclass]
#[pyclass(name = "FloatOverlayGraph", module = "i_overlay")]
pub struct PyFloatOverlayGraph {
    subject: Shapes,
    clip: Shapes,
    fill_rule: FillRule,
    options: PyOverlayOptions,
    solver: Option<PySolver>,
}

#[gen_stub_pymethods]
#[pymethods]
impl PyFloatOverlayGraph {
    /// Create a new FloatOverlayGraph from subject and clip shapes.
    ///
    /// Args:
    ///     subject: The subject shapes.
    ///     clip: The clip shapes.
    ///     fill_rule: The fill rule for determining filled regions.
    ///     options: Optional overlay options.
    ///     solver: Optional solver configuration.
    #[new]
    #[pyo3(signature = (subject, clip, fill_rule, *, options=None, solver=None))]
    fn new(
        subject: &Bound<'_, PyAny>,
        clip: &Bound<'_, PyAny>,
        fill_rule: PyFillRule,
        options: Option<PyOverlayOptions>,
        solver: Option<PySolver>,
    ) -> PyResult<Self> {
        let subj_shapes = extract_shapes(subject)?;
        let clip_shapes = extract_shapes(clip)?;

        Ok(Self {
            subject: subj_shapes,
            clip: clip_shapes,
            fill_rule: fill_rule.into(),
            options: options.unwrap_or_default(),
            solver,
        })
    }

    /// Extract shapes from the graph using the specified overlay rule.
    ///
    /// This method can be called multiple times with different overlay rules
    /// to extract different Boolean operation results from the same geometry.
    ///
    /// Args:
    ///     overlay_rule: The Boolean operation to perform.
    ///
    /// Returns:
    ///     The resulting shapes.
    fn extract_shapes(&self, py: Python<'_>, overlay_rule: PyOverlayRule) -> PyResult<Py<PyAny>> {
        let rust_options = build_overlay_options(&self.options);
        let solver = build_solver(self.solver.as_ref());

        let mut float_overlay =
            create_float_overlay(&self.subject, &self.clip, rust_options, solver);

        // Build graph and extract shapes
        let result = match float_overlay.build_graph_view(self.fill_rule) {
            Some(graph) => {
                let mut buffer = BooleanExtractionBuffer::default();
                graph.extract_shapes(overlay_rule.into(), &mut buffer)
            }
            None => Vec::new(),
        };

        shapes_to_python(py, &result)
    }

    fn __repr__(&self) -> String {
        format!(
            "FloatOverlayGraph(subject_count={}, clip_count={}, fill_rule={:?})",
            self.subject.len(),
            self.clip.len(),
            PyFillRule::from(self.fill_rule)
        )
    }
}
