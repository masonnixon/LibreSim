#!/bin/bash
# C compilation script for LibreSim Coder
# Uses CMake to build the project

set -e

PROJECT_DIR="${1:-/build/project}"
OUTPUT_DIR="${2:-/build/output}"

echo "=== LibreSim C Compiler ==="
echo "Project: $PROJECT_DIR"
echo "Output: $OUTPUT_DIR"

cd "$PROJECT_DIR"

# Create build directory
mkdir -p build
cd build

# Configure with CMake
echo "Configuring with CMake..."
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build
echo "Building..."
make -j$(nproc)

# Copy executable to output
echo "Copying executable..."
mkdir -p "$OUTPUT_DIR"

# Find the executable (usually named 'simulation' based on our CMakeLists.txt)
if [ -f "simulation" ]; then
    cp simulation "$OUTPUT_DIR/"
elif [ -f "bin/simulation" ]; then
    cp bin/simulation "$OUTPUT_DIR/"
else
    # Copy any executable found
    find . -type f -executable -name "simulation*" -exec cp {} "$OUTPUT_DIR/" \;
fi

echo "=== Compilation Complete ==="
ls -la "$OUTPUT_DIR"
