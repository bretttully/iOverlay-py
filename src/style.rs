//! Python wrappers for stroke and outline style configuration.

use pyo3::prelude::*;
use pyo3_stub_gen::derive::{gen_stub_pyclass, gen_stub_pymethods};
use std::f64::consts::PI;

use i_overlay_core::mesh::style::{LineCap, LineJoin, OutlineStyle, StrokeStyle};

use crate::enums::{PyLineCap, PyLineJoin};

/// Default angle for round caps and joins (radians).
/// Controls the segment length for approximating curves: L/R where L is segment length, R is radius.
const DEFAULT_ROUND_ANGLE: f64 = 0.1 * PI;

/// Default miter limit angle (radians).
/// For Miter joins, this is the minimum angle at which a miter is used.
/// At sharper angles (below this threshold), the join falls back to a bevel
/// to prevent extremely long, spiky miters.
const DEFAULT_MITER_ANGLE: f64 = 0.1 * PI;

/// Stroke style configuration for creating stroked paths.
///
/// Defines how a path is converted to a stroked shape with a specified width,
/// cap styles at the endpoints, and join styles at corners.
///
/// For custom caps, provide a list of points that define the cap shape.
/// Points should be relative to the stroke width, where the stroke extends
/// from -0.5 to 0.5 in the perpendicular direction.
#[gen_stub_pyclass]
#[pyclass(name = "StrokeStyle", module = "i_overlay", frozen)]
#[derive(Debug, Clone)]
pub struct PyStrokeStyle {
    /// The width of the stroke.
    #[pyo3(get)]
    pub width: f64,
    /// The cap style at the start of the stroke.
    #[pyo3(get)]
    pub start_cap: PyLineCap,
    /// The cap style at the end of the stroke.
    #[pyo3(get)]
    pub end_cap: PyLineCap,
    /// The join style where two lines meet.
    #[pyo3(get)]
    pub join: PyLineJoin,
    /// Angle parameter for round caps (radians).
    /// Controls curve approximation: smaller values = smoother curves with more segments.
    #[pyo3(get)]
    pub round_cap_angle: f64,
    /// Angle parameter for joins (radians).
    /// - For Round joins: controls curve approximation (smaller = smoother).
    /// - For Miter joins: minimum angle threshold; sharper corners fall back to bevel.
    #[pyo3(get)]
    pub join_angle: f64,
    /// Custom points for the start cap (overrides start_cap if provided).
    pub start_cap_points: Option<Vec<[f64; 2]>>,
    /// Custom points for the end cap (overrides end_cap if provided).
    pub end_cap_points: Option<Vec<[f64; 2]>>,
}

#[gen_stub_pymethods]
#[pymethods]
impl PyStrokeStyle {
    /// Create a new StrokeStyle with the given width.
    ///
    /// Note: The underlying Rust library clamps negative widths to 0.
    ///
    /// Args:
    ///     width: The stroke width.
    ///     start_cap: Cap style at the start (default: Butt).
    ///     end_cap: Cap style at the end (default: Butt).
    ///     join: Join style at corners (default: Bevel).
    ///     round_cap_angle: Angle for round caps in radians (default: ~0.314).
    ///         Smaller values produce smoother curves with more segments.
    ///     join_angle: Angle parameter for joins in radians (default: ~0.314).
    ///         For Round joins: smaller values = smoother curves.
    ///         For Miter joins: minimum angle threshold; sharper corners use bevel instead.
    ///     start_cap_points: Custom points for start cap (overrides start_cap).
    ///     end_cap_points: Custom points for end cap (overrides end_cap).
    #[new]
    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (width, *, start_cap=PyLineCap::Butt, end_cap=PyLineCap::Butt, join=PyLineJoin::Bevel, round_cap_angle=None, join_angle=None, start_cap_points=None, end_cap_points=None))]
    fn new(
        width: f64,
        start_cap: PyLineCap,
        end_cap: PyLineCap,
        join: PyLineJoin,
        round_cap_angle: Option<f64>,
        join_angle: Option<f64>,
        start_cap_points: Option<Vec<(f64, f64)>>,
        end_cap_points: Option<Vec<(f64, f64)>>,
    ) -> Self {
        Self {
            width,
            start_cap,
            end_cap,
            join,
            round_cap_angle: round_cap_angle.unwrap_or(DEFAULT_ROUND_ANGLE),
            join_angle: join_angle.unwrap_or(DEFAULT_MITER_ANGLE),
            start_cap_points: start_cap_points
                .map(|pts| pts.into_iter().map(|(x, y)| [x, y]).collect()),
            end_cap_points: end_cap_points
                .map(|pts| pts.into_iter().map(|(x, y)| [x, y]).collect()),
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "StrokeStyle(width={}, start_cap={:?}, end_cap={:?}, join={:?})",
            self.width, self.start_cap, self.end_cap, self.join
        )
    }
}

impl PyStrokeStyle {
    /// Convert to Rust StrokeStyle.
    pub fn to_rust_style(&self) -> StrokeStyle<[f64; 2], f64> {
        // Use custom cap points if provided, otherwise use the cap style
        let start_cap = if let Some(ref points) = self.start_cap_points {
            LineCap::Custom(points.clone())
        } else {
            match self.start_cap {
                PyLineCap::Butt => LineCap::Butt,
                PyLineCap::Round => LineCap::Round(self.round_cap_angle),
                PyLineCap::Square => LineCap::Square,
            }
        };

        let end_cap = if let Some(ref points) = self.end_cap_points {
            LineCap::Custom(points.clone())
        } else {
            match self.end_cap {
                PyLineCap::Butt => LineCap::Butt,
                PyLineCap::Round => LineCap::Round(self.round_cap_angle),
                PyLineCap::Square => LineCap::Square,
            }
        };

        let join = match self.join {
            PyLineJoin::Bevel => LineJoin::Bevel,
            PyLineJoin::Miter => LineJoin::Miter(self.join_angle),
            PyLineJoin::Round => LineJoin::Round(self.join_angle),
        };

        StrokeStyle {
            width: self.width,
            start_cap,
            end_cap,
            join,
        }
    }
}

/// Outline style configuration for creating offset shapes.
///
/// Defines how a shape's boundary is offset inward and/or outward
/// to create a thickened outline.
#[gen_stub_pyclass]
#[pyclass(name = "OutlineStyle", module = "i_overlay", frozen)]
#[derive(Debug, Clone)]
pub struct PyOutlineStyle {
    /// The outer offset distance.
    #[pyo3(get)]
    pub outer_offset: f64,
    /// The inner offset distance.
    #[pyo3(get)]
    pub inner_offset: f64,
    /// The join style at corners.
    #[pyo3(get)]
    pub join: PyLineJoin,
    /// Angle parameter for joins (radians).
    /// - For Round joins: controls curve approximation (smaller = smoother).
    /// - For Miter joins: minimum angle threshold; sharper corners fall back to bevel.
    #[pyo3(get)]
    pub join_angle: f64,
}

#[gen_stub_pymethods]
#[pymethods]
impl PyOutlineStyle {
    /// Create a new OutlineStyle with the given offset.
    ///
    /// Args:
    ///     offset: The offset distance (used for both inner and outer if not specified separately).
    ///     outer_offset: The outer offset distance (overrides offset if specified).
    ///     inner_offset: The inner offset distance (overrides offset if specified).
    ///     join: Join style at corners (default: Bevel).
    ///     join_angle: Angle parameter for joins in radians (default: ~0.314).
    ///         For Round joins: smaller values = smoother curves.
    ///         For Miter joins: minimum angle threshold; sharper corners use bevel instead.
    #[new]
    #[pyo3(signature = (offset=1.0, *, outer_offset=None, inner_offset=None, join=PyLineJoin::Bevel, join_angle=None))]
    fn new(
        offset: f64,
        outer_offset: Option<f64>,
        inner_offset: Option<f64>,
        join: PyLineJoin,
        join_angle: Option<f64>,
    ) -> Self {
        Self {
            outer_offset: outer_offset.unwrap_or(offset),
            inner_offset: inner_offset.unwrap_or(offset),
            join,
            join_angle: join_angle.unwrap_or(DEFAULT_MITER_ANGLE),
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "OutlineStyle(outer_offset={}, inner_offset={}, join={:?})",
            self.outer_offset, self.inner_offset, self.join
        )
    }
}

impl PyOutlineStyle {
    /// Convert to Rust OutlineStyle.
    pub fn to_rust_style(&self) -> OutlineStyle<f64> {
        let join = match self.join {
            PyLineJoin::Bevel => LineJoin::Bevel,
            PyLineJoin::Miter => LineJoin::Miter(self.join_angle),
            PyLineJoin::Round => LineJoin::Round(self.join_angle),
        };

        OutlineStyle {
            outer_offset: self.outer_offset,
            inner_offset: self.inner_offset,
            join,
        }
    }
}
