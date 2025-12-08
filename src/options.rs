//! Python wrappers for iOverlay configuration types.

use pyo3::prelude::*;
use pyo3_stub_gen::derive::{gen_stub_pyclass, gen_stub_pymethods};

use crate::enums::{PyContourDirection, PyStrategy};
use i_overlay_core::core::overlay::{ContourDirection, IntOverlayOptions};
use i_overlay_core::core::solver::{MultithreadOptions, Precision, Solver, Strategy};

/// Precision level for the solver to determine tolerance for snapping to edge ends.
///
/// The precision determines a radius calculated as `2^value`, where `value` starts
/// at `start` and increases by `progression` in each iteration.
#[gen_stub_pyclass]
#[pyclass(name = "Precision", module = "i_overlay", frozen, eq, hash)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct PyPrecision {
    /// The initial exponent value for the radius calculation.
    #[pyo3(get)]
    pub start: usize,
    /// The amount by which the exponent increases in each iteration.
    #[pyo3(get)]
    pub progression: usize,
}

#[gen_stub_pymethods]
#[pymethods]
impl PyPrecision {
    /// Create a new Precision with the given start and progression values.
    #[new]
    #[pyo3(signature = (start=0, progression=1))]
    fn new(start: usize, progression: usize) -> Self {
        Self { start, progression }
    }

    /// Absolute precision with no progression (radius remains at 2^0 = 1).
    #[classattr]
    const ABSOLUTE: PyPrecision = PyPrecision {
        start: 0,
        progression: 0,
    };

    /// High precision, starting at 2^0 = 1 and doubling every loop.
    #[classattr]
    const HIGH: PyPrecision = PyPrecision {
        start: 0,
        progression: 1,
    };

    /// Medium-high precision, starting at 2^1 = 2 and doubling every loop.
    #[classattr]
    const MEDIUM_HIGH: PyPrecision = PyPrecision {
        start: 1,
        progression: 1,
    };

    /// Medium precision, starting at 2^0 = 1 and quadrupling every loop.
    #[classattr]
    const MEDIUM: PyPrecision = PyPrecision {
        start: 0,
        progression: 2,
    };

    /// Medium-low precision, starting at 2^2 = 4 and quadrupling every loop.
    #[classattr]
    const MEDIUM_LOW: PyPrecision = PyPrecision {
        start: 2,
        progression: 2,
    };

    /// Low precision, starting at 2^2 = 4 and increasing by factor of 8 every loop.
    #[classattr]
    const LOW: PyPrecision = PyPrecision {
        start: 2,
        progression: 3,
    };

    fn __repr__(&self) -> String {
        format!(
            "Precision(start={}, progression={})",
            self.start, self.progression
        )
    }
}

impl From<PyPrecision> for Precision {
    fn from(value: PyPrecision) -> Self {
        Precision {
            start: value.start,
            progression: value.progression,
        }
    }
}

impl From<Precision> for PyPrecision {
    fn from(value: Precision) -> Self {
        PyPrecision {
            start: value.start,
            progression: value.progression,
        }
    }
}

/// Solver configuration for geometric processing algorithms.
///
/// Controls the strategy, precision, and multithreading options for Boolean operations.
#[gen_stub_pyclass]
#[pyclass(name = "Solver", module = "i_overlay", frozen)]
#[derive(Debug, Clone)]
pub struct PySolver {
    /// The algorithm strategy to use.
    #[pyo3(get)]
    pub strategy: PyStrategy,
    /// The precision level for snapping operations.
    #[pyo3(get)]
    pub precision: PyPrecision,
    /// Whether multithreading is enabled.
    #[pyo3(get)]
    pub multithreading: bool,
}

#[gen_stub_pymethods]
#[pymethods]
impl PySolver {
    /// Create a new Solver with the given configuration.
    #[new]
    #[pyo3(signature = (strategy=PyStrategy::Auto, precision=None, multithreading=true))]
    fn new(strategy: PyStrategy, precision: Option<PyPrecision>, multithreading: bool) -> Self {
        Self {
            strategy,
            precision: precision.unwrap_or(PyPrecision::HIGH),
            multithreading,
        }
    }

    /// Solver using list-based approach with high precision.
    #[classattr]
    #[allow(non_snake_case)]
    fn LIST() -> PySolver {
        PySolver {
            strategy: PyStrategy::List,
            precision: PyPrecision::HIGH,
            multithreading: true,
        }
    }

    /// Solver using tree-based approach with high precision.
    #[classattr]
    #[allow(non_snake_case)]
    fn TREE() -> PySolver {
        PySolver {
            strategy: PyStrategy::Tree,
            precision: PyPrecision::HIGH,
            multithreading: true,
        }
    }

    /// Solver using fragment-based approach with high precision.
    #[classattr]
    #[allow(non_snake_case)]
    fn FRAG() -> PySolver {
        PySolver {
            strategy: PyStrategy::Frag,
            precision: PyPrecision::HIGH,
            multithreading: true,
        }
    }

    /// Solver with automatic strategy selection (recommended).
    #[classattr]
    #[allow(non_snake_case)]
    fn AUTO() -> PySolver {
        PySolver {
            strategy: PyStrategy::Auto,
            precision: PyPrecision::HIGH,
            multithreading: true,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "Solver(strategy={:?}, precision={:?}, multithreading={})",
            self.strategy, self.precision, self.multithreading
        )
    }
}

impl From<&PySolver> for Solver {
    fn from(value: &PySolver) -> Self {
        Solver {
            strategy: Strategy::from(value.strategy),
            precision: Precision::from(value.precision),
            multithreading: if value.multithreading {
                Some(MultithreadOptions::default())
            } else {
                None
            },
        }
    }
}

/// Configuration options for polygon Boolean operations.
///
/// Controls precision, simplification, and contour filtering during Boolean operations.
#[gen_stub_pyclass]
#[pyclass(name = "OverlayOptions", module = "i_overlay", frozen)]
#[derive(Debug, Clone)]
pub struct PyOverlayOptions {
    /// Preserve collinear points in the input before Boolean operations.
    #[pyo3(get)]
    pub preserve_input_collinear: bool,
    /// Desired direction for output contours.
    #[pyo3(get)]
    pub output_direction: PyContourDirection,
    /// Preserve collinear points in the output after Boolean operations.
    #[pyo3(get)]
    pub preserve_output_collinear: bool,
    /// Minimum area threshold to include a contour in the result.
    #[pyo3(get)]
    pub min_output_area: u64,
}

#[gen_stub_pymethods]
#[pymethods]
impl PyOverlayOptions {
    /// Create new OverlayOptions with the given configuration.
    #[new]
    #[pyo3(signature = (
        preserve_input_collinear=false,
        output_direction=PyContourDirection::CounterClockwise,
        preserve_output_collinear=false,
        min_output_area=0
    ))]
    fn new(
        preserve_input_collinear: bool,
        output_direction: PyContourDirection,
        preserve_output_collinear: bool,
        min_output_area: u64,
    ) -> Self {
        Self {
            preserve_input_collinear,
            output_direction,
            preserve_output_collinear,
            min_output_area,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "OverlayOptions(preserve_input_collinear={}, output_direction={:?}, preserve_output_collinear={}, min_output_area={})",
            self.preserve_input_collinear, self.output_direction, self.preserve_output_collinear, self.min_output_area
        )
    }
}

impl Default for PyOverlayOptions {
    fn default() -> Self {
        Self {
            preserve_input_collinear: false,
            output_direction: PyContourDirection::CounterClockwise,
            preserve_output_collinear: false,
            min_output_area: 0,
        }
    }
}

impl From<&PyOverlayOptions> for IntOverlayOptions {
    fn from(value: &PyOverlayOptions) -> Self {
        IntOverlayOptions {
            preserve_input_collinear: value.preserve_input_collinear,
            output_direction: ContourDirection::from(value.output_direction),
            preserve_output_collinear: value.preserve_output_collinear,
            min_output_area: value.min_output_area,
        }
    }
}
