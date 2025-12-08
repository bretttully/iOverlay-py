//! Python wrapper for ClipRule configuration.

use pyo3::prelude::*;
use pyo3_stub_gen::derive::{gen_stub_pyclass, gen_stub_pymethods};

use i_overlay_core::string::clip::ClipRule;

/// Configuration for clipping lines with rules to determine inclusion or exclusion.
///
/// Controls how lines are clipped against polygon boundaries.
#[gen_stub_pyclass]
#[pyclass(name = "ClipRule", module = "i_overlay", frozen, eq, hash)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct PyClipRule {
    /// If true, inverts the clipping area selection.
    #[pyo3(get)]
    pub invert: bool,
    /// If true, includes boundary lines in the clipping result.
    #[pyo3(get)]
    pub boundary_included: bool,
}

#[gen_stub_pymethods]
#[pymethods]
impl PyClipRule {
    /// Create a new ClipRule with the given configuration.
    #[new]
    #[pyo3(signature = (invert=false, boundary_included=true))]
    fn new(invert: bool, boundary_included: bool) -> Self {
        Self {
            invert,
            boundary_included,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "ClipRule(invert={}, boundary_included={})",
            self.invert, self.boundary_included
        )
    }
}

impl From<PyClipRule> for ClipRule {
    fn from(value: PyClipRule) -> Self {
        ClipRule {
            invert: value.invert,
            boundary_included: value.boundary_included,
        }
    }
}

impl From<ClipRule> for PyClipRule {
    fn from(value: ClipRule) -> Self {
        PyClipRule {
            invert: value.invert,
            boundary_included: value.boundary_included,
        }
    }
}
