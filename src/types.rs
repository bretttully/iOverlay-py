//! Type definitions and conversions for Python bindings.
//!
//! Provides conversion utilities between Python types and Rust types
//! for geometric data structures.

use pyo3::prelude::*;
use pyo3::types::PyAny;

/// Type alias for a point as [x, y] coordinates.
pub type Point = [f64; 2];

/// Type alias for a contour (closed path) as a list of points.
pub type Contour = Vec<Point>;

/// Type alias for a shape (contour with optional holes).
/// First contour is the outer boundary, subsequent contours are holes.
pub type Shape = Vec<Contour>;

/// Type alias for a collection of shapes.
pub type Shapes = Vec<Shape>;

/// Type alias for an open path.
#[allow(dead_code)]
pub type Path = Vec<Point>;

/// Type alias for a collection of paths.
#[allow(dead_code)]
pub type Paths = Vec<Path>;

/// Extracts shapes from a Python object.
///
/// Accepts shapes in the format:
/// - `list[list[list[tuple[float, float]]]]` (full shapes format)
/// - The structure is: Shapes > Shape > Contour > Point (x, y)
pub fn extract_shapes(obj: &Bound<'_, PyAny>) -> PyResult<Shapes> {
    let py_shapes: Vec<Bound<'_, PyAny>> = obj.extract()?;
    let mut shapes = Vec::with_capacity(py_shapes.len());

    for py_shape in py_shapes {
        let py_contours: Vec<Bound<'_, PyAny>> = py_shape.extract()?;
        let mut shape = Vec::with_capacity(py_contours.len());

        for py_contour in py_contours {
            let contour = extract_contour(&py_contour)?;
            shape.push(contour);
        }
        shapes.push(shape);
    }

    Ok(shapes)
}

/// Extracts a single contour from a Python object.
fn extract_contour(obj: &Bound<'_, PyAny>) -> PyResult<Contour> {
    let py_points: Vec<Bound<'_, PyAny>> = obj.extract()?;
    let mut contour = Vec::with_capacity(py_points.len());

    for py_point in py_points {
        let point: (f64, f64) = py_point.extract()?;
        contour.push([point.0, point.1]);
    }

    Ok(contour)
}

/// Converts Rust shapes to Python format.
///
/// Returns shapes as `list[list[list[tuple[float, float]]]]`
pub fn shapes_to_python(py: Python<'_>, shapes: &Shapes) -> PyResult<Py<PyAny>> {
    let py_shapes: Vec<Py<PyAny>> = shapes
        .iter()
        .map(|shape| shape_to_python(py, shape))
        .collect::<PyResult<Vec<_>>>()?;

    Ok(py_shapes.into_pyobject(py)?.unbind())
}

/// Converts a single Rust shape to Python format.
fn shape_to_python(py: Python<'_>, shape: &Shape) -> PyResult<Py<PyAny>> {
    let py_contours: Vec<Py<PyAny>> = shape
        .iter()
        .map(|contour| contour_to_python(py, contour))
        .collect::<PyResult<Vec<_>>>()?;

    Ok(py_contours.into_pyobject(py)?.unbind())
}

/// Converts a single contour to Python format.
fn contour_to_python(py: Python<'_>, contour: &Contour) -> PyResult<Py<PyAny>> {
    let py_points: Vec<(f64, f64)> = contour.iter().map(|p| (p[0], p[1])).collect();

    Ok(py_points.into_pyobject(py)?.unbind())
}

/// Extracts paths from a Python object.
///
/// Accepts paths in the format:
/// - `list[list[tuple[float, float]]]`
#[allow(dead_code)]
pub fn extract_paths(obj: &Bound<'_, PyAny>) -> PyResult<Paths> {
    let py_paths: Vec<Bound<'_, PyAny>> = obj.extract()?;
    let mut paths = Vec::with_capacity(py_paths.len());

    for py_path in py_paths {
        let path = extract_contour(&py_path)?;
        paths.push(path);
    }

    Ok(paths)
}

/// Converts Rust paths to Python format.
#[allow(dead_code)]
pub fn paths_to_python(py: Python<'_>, paths: &Paths) -> PyResult<Py<PyAny>> {
    let py_paths: Vec<Py<PyAny>> = paths
        .iter()
        .map(|path| contour_to_python(py, path))
        .collect::<PyResult<Vec<_>>>()?;

    Ok(py_paths.into_pyobject(py)?.unbind())
}
