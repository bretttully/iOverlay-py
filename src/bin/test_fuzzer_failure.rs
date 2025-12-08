//! Test fuzzer failure directly against raw Rust implementation.
//!
//! This binary reads a fuzzer failure JSON file and tests the raw Rust
//! i_overlay implementation to determine if the failure is in:
//! 1. The Python bindings
//! 2. The upstream Rust library
//!
//! Usage:
//!     cargo run --bin test_fuzzer_failure -- fuzzer_failures/fuzzer-spots-12.json
//!
//! The JSON file should have the format:
//! {
//!     "generator": "spots",
//!     "seed": 12,
//!     "subject": [[[(x, y), ...], ...], ...],
//!     "clip": [[[(x, y), ...], ...], ...],
//!     "errors": [{"function": "...", "error": "...", ...}, ...]
//! }

use std::env;
use std::fs;
use std::process::ExitCode;

use i_overlay_core::core::fill_rule::FillRule;
use i_overlay_core::core::overlay_rule::OverlayRule;
use i_overlay_core::float::overlay::FloatOverlay;

use serde::Deserialize;

/// A point as [x, y] array
type Point = [f64; 2];
/// A contour (ring) is a list of points
type Contour = Vec<Point>;
/// A shape has an exterior ring and optional hole rings
type Shape = Vec<Contour>;
/// Shapes is a list of shapes
type Shapes = Vec<Shape>;

#[derive(Debug, Deserialize)]
struct FuzzerFailure {
    generator: String,
    seed: i64,
    subject: Shapes,
    clip: Shapes,
    errors: Vec<ErrorRecord>,
}

#[derive(Debug, Deserialize)]
struct ErrorRecord {
    function: String,
    error: Option<String>,
}

/// All overlay rules to test
const OVERLAY_RULES: &[(OverlayRule, &str)] = &[
    (OverlayRule::Union, "Union"),
    (OverlayRule::Intersect, "Intersect"),
    (OverlayRule::Difference, "Difference"),
    (OverlayRule::Xor, "Xor"),
];

/// All fill rules to test
const FILL_RULES: &[(FillRule, &str)] = &[
    (FillRule::EvenOdd, "EvenOdd"),
    (FillRule::NonZero, "NonZero"),
    (FillRule::Positive, "Positive"),
    (FillRule::Negative, "Negative"),
];

/// Run overlay operation and return result or error
fn test_overlay(
    subject: &Shapes,
    clip: &Shapes,
    overlay_rule: OverlayRule,
    fill_rule: FillRule,
) -> Result<Shapes, String> {
    // Use catch_unwind to handle panics
    let result = std::panic::catch_unwind(|| {
        let mut overlay = FloatOverlay::with_subj_and_clip(subject, clip);
        overlay.overlay(overlay_rule, fill_rule)
    });

    match result {
        Ok(shapes) => Ok(shapes),
        Err(e) => {
            let msg = if let Some(s) = e.downcast_ref::<&str>() {
                s.to_string()
            } else if let Some(s) = e.downcast_ref::<String>() {
                s.clone()
            } else {
                "Unknown panic".to_string()
            };
            Err(format!("Panic: {}", msg))
        }
    }
}

/// Validate the result shapes (basic sanity checks)
fn validate_result(shapes: &Shapes) -> Result<(), String> {
    for (i, shape) in shapes.iter().enumerate() {
        if shape.is_empty() {
            return Err(format!("Shape {} has no contours", i));
        }
        for (j, contour) in shape.iter().enumerate() {
            if contour.len() < 3 {
                return Err(format!(
                    "Shape {} contour {} has only {} points (need >= 3)",
                    i,
                    j,
                    contour.len()
                ));
            }
            // Check for NaN or infinite values
            for (k, point) in contour.iter().enumerate() {
                if !point[0].is_finite() || !point[1].is_finite() {
                    return Err(format!(
                        "Shape {} contour {} point {} has non-finite value: {:?}",
                        i, j, k, point
                    ));
                }
            }
        }
    }
    Ok(())
}

/// Calculate simple area for debugging
fn calculate_area(shapes: &Shapes) -> f64 {
    let mut total = 0.0;
    for shape in shapes {
        for contour in shape {
            let n = contour.len();
            if n < 3 {
                continue;
            }
            let mut area = 0.0;
            for i in 0..n {
                let j = (i + 1) % n;
                area += contour[i][0] * contour[j][1];
                area -= contour[j][0] * contour[i][1];
            }
            total += area.abs() / 2.0;
        }
    }
    total
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        eprintln!("Usage: {} <fuzzer_failure.json>", args[0]);
        eprintln!();
        eprintln!("Tests a fuzzer failure JSON file against the raw Rust i_overlay implementation");
        eprintln!("to determine if the failure is in the bindings or the upstream library.");
        return ExitCode::from(1);
    }

    let json_path = &args[1];

    // Read and parse the JSON file
    let json_content = match fs::read_to_string(json_path) {
        Ok(content) => content,
        Err(e) => {
            eprintln!("Error reading file '{}': {}", json_path, e);
            return ExitCode::from(1);
        }
    };

    let failure: FuzzerFailure = match serde_json::from_str(&json_content) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("Error parsing JSON: {}", e);
            return ExitCode::from(1);
        }
    };

    println!("=== Fuzzer Failure Test ===");
    println!("Generator: {}", failure.generator);
    println!("Seed: {}", failure.seed);
    println!("Subject shapes: {}", failure.subject.len());
    println!("Clip shapes: {}", failure.clip.len());
    println!();

    // Print original errors from Python
    println!("Original Python errors:");
    for err in &failure.errors {
        if let Some(ref error_msg) = err.error {
            println!("  {}: {}", err.function, error_msg);
        }
    }
    println!();

    // Test all combinations
    println!("Testing raw Rust implementation:");
    let mut rust_errors = Vec::new();
    let mut rust_successes = 0;

    for (overlay_rule, overlay_name) in OVERLAY_RULES {
        for (fill_rule, fill_name) in FILL_RULES {
            let test_name = format!("{}_{}", overlay_name, fill_name);

            match test_overlay(&failure.subject, &failure.clip, *overlay_rule, *fill_rule) {
                Ok(result) => {
                    // Validate the result
                    match validate_result(&result) {
                        Ok(()) => {
                            let area = calculate_area(&result);
                            println!(
                                "  {} \x1b[32mOK\x1b[0m (shapes={}, area={:.2})",
                                test_name,
                                result.len(),
                                area
                            );
                            rust_successes += 1;
                        }
                        Err(validation_error) => {
                            println!(
                                "  {} \x1b[33mWARN\x1b[0m validation: {}",
                                test_name, validation_error
                            );
                            rust_errors.push((test_name.clone(), validation_error));
                        }
                    }
                }
                Err(e) => {
                    println!("  {} \x1b[31mFAIL\x1b[0m {}", test_name, e);
                    rust_errors.push((test_name.clone(), e));
                }
            }
        }
    }

    println!();
    println!("=== Summary ===");
    println!("Rust successes: {}", rust_successes);
    println!("Rust errors: {}", rust_errors.len());

    if rust_errors.is_empty() {
        println!();
        println!(
            "\x1b[32mConclusion: All Rust tests passed. The failure is likely in the Python bindings\x1b[0m"
        );
        println!(
            "or in the shapely validation (geometry may be valid for i_overlay but not shapely)."
        );
    } else {
        println!();
        println!("\x1b[31mConclusion: Rust implementation also has failures.\x1b[0m");
        println!("This is an upstream issue with i_overlay, not the Python bindings.");
        println!();
        println!("Failing tests:");
        for (name, error) in &rust_errors {
            println!("  {}: {}", name, error);
        }
    }

    if rust_errors.is_empty() {
        ExitCode::from(0)
    } else {
        ExitCode::from(1)
    }
}
