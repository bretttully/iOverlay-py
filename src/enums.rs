//! Python enum wrappers for iOverlay types.

use pyo3::prelude::*;
use pyo3_stub_gen::derive::gen_stub_pyclass_enum;

use i_overlay_core::core::fill_rule::FillRule;
use i_overlay_core::core::overlay::ContourDirection;
use i_overlay_core::core::overlay::ShapeType;
use i_overlay_core::core::overlay_rule::OverlayRule;
use i_overlay_core::core::solver::Strategy;

/// Represents the rule used to determine the "fill" of a shape.
///
/// - `EvenOdd`: Only odd-numbered sub-regions are filled.
/// - `NonZero`: Only non-zero sub-regions are filled (default).
/// - `Positive`: Fills regions where the winding number is positive.
/// - `Negative`: Fills regions where the winding number is negative.
#[gen_stub_pyclass_enum]
#[pyclass(name = "FillRule", module = "i_overlay", frozen, eq, eq_int, hash)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum PyFillRule {
    /// Only odd-numbered sub-regions are filled.
    EvenOdd = 0,
    /// Only non-zero sub-regions are filled (default).
    NonZero = 1,
    /// Fills regions where the winding number is positive.
    Positive = 2,
    /// Fills regions where the winding number is negative.
    Negative = 3,
}

impl From<PyFillRule> for FillRule {
    fn from(value: PyFillRule) -> Self {
        match value {
            PyFillRule::EvenOdd => FillRule::EvenOdd,
            PyFillRule::NonZero => FillRule::NonZero,
            PyFillRule::Positive => FillRule::Positive,
            PyFillRule::Negative => FillRule::Negative,
        }
    }
}

impl From<FillRule> for PyFillRule {
    fn from(value: FillRule) -> Self {
        match value {
            FillRule::EvenOdd => PyFillRule::EvenOdd,
            FillRule::NonZero => PyFillRule::NonZero,
            FillRule::Positive => PyFillRule::Positive,
            FillRule::Negative => PyFillRule::Negative,
        }
    }
}

/// Defines the types of overlay/boolean operations that can be applied to shapes.
///
/// - `Subject`: Processes the subject shape (resolves self-intersections).
/// - `Clip`: Similar to Subject, but for clip shapes.
/// - `Intersect`: Finds the common area between subject and clip (A ∩ B).
/// - `Union`: Combines both shapes into one (A ∪ B).
/// - `Difference`: Subtracts clip from subject (A - B).
/// - `InverseDifference`: Subtracts subject from clip (B - A).
/// - `Xor`: Areas unique to each shape, excluding overlap (A ⊕ B).
#[gen_stub_pyclass_enum]
#[pyclass(name = "OverlayRule", module = "i_overlay", frozen, eq, eq_int, hash)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum PyOverlayRule {
    /// Processes the subject shape (resolves self-intersections).
    Subject = 0,
    /// Processes the clip shape (resolves self-intersections).
    Clip = 1,
    /// Finds the common area between subject and clip (A ∩ B).
    Intersect = 2,
    /// Combines both shapes into one (A ∪ B).
    Union = 3,
    /// Subtracts clip from subject (A - B).
    Difference = 4,
    /// Subtracts subject from clip (B - A).
    InverseDifference = 5,
    /// Areas unique to each shape, excluding overlap (A ⊕ B).
    Xor = 6,
}

impl From<PyOverlayRule> for OverlayRule {
    fn from(value: PyOverlayRule) -> Self {
        match value {
            PyOverlayRule::Subject => OverlayRule::Subject,
            PyOverlayRule::Clip => OverlayRule::Clip,
            PyOverlayRule::Intersect => OverlayRule::Intersect,
            PyOverlayRule::Union => OverlayRule::Union,
            PyOverlayRule::Difference => OverlayRule::Difference,
            PyOverlayRule::InverseDifference => OverlayRule::InverseDifference,
            PyOverlayRule::Xor => OverlayRule::Xor,
        }
    }
}

impl From<OverlayRule> for PyOverlayRule {
    fn from(value: OverlayRule) -> Self {
        match value {
            OverlayRule::Subject => PyOverlayRule::Subject,
            OverlayRule::Clip => PyOverlayRule::Clip,
            OverlayRule::Intersect => PyOverlayRule::Intersect,
            OverlayRule::Union => PyOverlayRule::Union,
            OverlayRule::Difference => PyOverlayRule::Difference,
            OverlayRule::InverseDifference => PyOverlayRule::InverseDifference,
            OverlayRule::Xor => PyOverlayRule::Xor,
        }
    }
}

/// Represents the winding direction of a contour.
///
/// - `CounterClockwise`: Default for outer boundaries.
/// - `Clockwise`: Default for holes.
#[gen_stub_pyclass_enum]
#[pyclass(
    name = "ContourDirection",
    module = "i_overlay",
    frozen,
    eq,
    eq_int,
    hash
)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum PyContourDirection {
    /// Counter-clockwise winding (default for outer boundaries).
    CounterClockwise = 0,
    /// Clockwise winding (default for holes).
    Clockwise = 1,
}

impl From<PyContourDirection> for ContourDirection {
    fn from(value: PyContourDirection) -> Self {
        match value {
            PyContourDirection::CounterClockwise => ContourDirection::CounterClockwise,
            PyContourDirection::Clockwise => ContourDirection::Clockwise,
        }
    }
}

impl From<ContourDirection> for PyContourDirection {
    fn from(value: ContourDirection) -> Self {
        match value {
            ContourDirection::CounterClockwise => PyContourDirection::CounterClockwise,
            ContourDirection::Clockwise => PyContourDirection::Clockwise,
        }
    }
}

/// Specifies the type of shape being processed in Boolean operations.
///
/// - `Subject`: The primary shape(s), acts as the base layer.
/// - `Clip`: The modifying shape(s) applied to the subject.
///
/// Note: All operations except Difference are commutative.
#[gen_stub_pyclass_enum]
#[pyclass(name = "ShapeType", module = "i_overlay", frozen, eq, eq_int, hash)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum PyShapeType {
    /// The primary shape(s) for operations.
    Subject = 0,
    /// The modifying shape(s) applied to the subject.
    Clip = 1,
}

impl From<PyShapeType> for ShapeType {
    fn from(value: PyShapeType) -> Self {
        match value {
            PyShapeType::Subject => ShapeType::Subject,
            PyShapeType::Clip => ShapeType::Clip,
        }
    }
}

impl From<ShapeType> for PyShapeType {
    fn from(value: ShapeType) -> Self {
        match value {
            ShapeType::Subject => PyShapeType::Subject,
            ShapeType::Clip => PyShapeType::Clip,
        }
    }
}

/// Represents the algorithm strategy for processing geometric data.
///
/// - `List`: Linear list-based approach, better for <10,000 edges.
/// - `Tree`: Tree-based structure, better for larger datasets.
/// - `Frag`: Fragment-based strategy.
/// - `Auto`: Automatically selects the best strategy (recommended).
#[gen_stub_pyclass_enum]
#[pyclass(name = "Strategy", module = "i_overlay", frozen, eq, eq_int, hash)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum PyStrategy {
    /// Linear list-based approach, better for smaller datasets.
    List = 0,
    /// Tree-based structure, better for larger datasets.
    Tree = 1,
    /// Fragment-based strategy.
    Frag = 2,
    /// Automatically selects the best strategy (recommended).
    Auto = 3,
}

impl From<PyStrategy> for Strategy {
    fn from(value: PyStrategy) -> Self {
        match value {
            PyStrategy::List => Strategy::List,
            PyStrategy::Tree => Strategy::Tree,
            PyStrategy::Frag => Strategy::Frag,
            PyStrategy::Auto => Strategy::Auto,
        }
    }
}

impl From<Strategy> for PyStrategy {
    fn from(value: Strategy) -> Self {
        match value {
            Strategy::List => PyStrategy::List,
            Strategy::Tree => PyStrategy::Tree,
            Strategy::Frag => PyStrategy::Frag,
            Strategy::Auto => PyStrategy::Auto,
        }
    }
}

/// The endpoint style of a line.
///
/// - `Butt`: Squared-off end (default).
/// - `Round`: Rounded end with semicircular arc.
/// - `Square`: Squared-off end extended by half line width.
#[gen_stub_pyclass_enum]
#[pyclass(name = "LineCap", module = "i_overlay", frozen, eq, eq_int, hash)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum PyLineCap {
    /// A line with a squared-off end (default).
    Butt = 0,
    /// A line with a rounded end.
    Round = 1,
    /// A line with a squared-off end, extended by half the line width.
    Square = 2,
}

/// The join style where two lines meet.
///
/// - `Bevel`: Cuts off the corner (default).
/// - `Miter`: Creates a sharp corner.
/// - `Round`: Creates an arc corner.
#[gen_stub_pyclass_enum]
#[pyclass(name = "LineJoin", module = "i_overlay", frozen, eq, eq_int, hash)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum PyLineJoin {
    /// Cuts off the corner where two lines meet (default).
    Bevel = 0,
    /// Creates a sharp corner where two lines meet.
    Miter = 1,
    /// Creates an arc corner where two lines meet.
    Round = 2,
}
