#!/bin/bash
# Rust compilation script for LibreSim Coder
# Uses Cargo to build the project

set -e

PROJECT_DIR="${1:-/build/project}"
OUTPUT_DIR="${2:-/build/output}"

echo "=== LibreSim Rust Compiler ==="
echo "Project: $PROJECT_DIR"
echo "Output: $OUTPUT_DIR"

cd "$PROJECT_DIR"

# Build with Cargo in release mode
echo "Building with Cargo..."
cargo build --release

# Copy executable to output
echo "Copying executable..."
mkdir -p "$OUTPUT_DIR"

# The executable is in target/release/
if [ -f "target/release/simulation" ]; then
    cp target/release/simulation "$OUTPUT_DIR/"
else
    # Find any executable in target/release
    find target/release -maxdepth 1 -type f -executable ! -name "*.d" -exec cp {} "$OUTPUT_DIR/" \;
fi

echo "=== Compilation Complete ==="
ls -la "$OUTPUT_DIR"
