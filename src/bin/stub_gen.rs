//! Stub generator binary for i_overlay Python bindings
//!
//! Generates .pyi stub files for IDE type checking and autocompletion.
//!
//! Usage:
//!     cargo run --bin stub_gen
//!
//! This will generate `i_overlay.pyi` in the project root.

use pyo3_stub_gen::Result;
use std::fs;

fn main() -> Result<()> {
    // Get the stub info from the library
    let stub = i_overlay::stub_info()?;
    // Generate the stub file
    stub.generate()?;

    // Post-process the generated stub file to add missing elements
    let stub_path = "i_overlay.pyi";
    let content = fs::read_to_string(stub_path)?;

    // Add __version__ at the top of the module (after the imports)
    let content = content.replace(
        "import typing\n\n@typing.final",
        "import typing\n\n__version__: str\n\n@typing.final",
    );

    fs::write(stub_path, content)?;

    Ok(())
}
