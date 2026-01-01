#!/bin/bash
# Python compilation script for LibreSim Coder
# Uses PyInstaller to create standalone executable

set -e

PROJECT_DIR="${1:-/build/project}"
OUTPUT_DIR="${2:-/build/output}"

echo "=== LibreSim Python Compiler ==="
echo "Project: $PROJECT_DIR"
echo "Output: $OUTPUT_DIR"

cd "$PROJECT_DIR"

# Install project dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install --no-cache-dir -r requirements.txt
fi

# Find the main entry point
MAIN_FILE=""
if [ -f "main.py" ]; then
    MAIN_FILE="main.py"
elif [ -f "src/main.py" ]; then
    MAIN_FILE="src/main.py"
else
    echo "Error: No main.py found"
    exit 1
fi

echo "Compiling $MAIN_FILE..."

# Use PyInstaller to create standalone executable
pyinstaller \
    --onefile \
    --distpath "$OUTPUT_DIR" \
    --workpath /tmp/pyinstaller \
    --specpath /tmp/pyinstaller \
    --name simulation \
    "$MAIN_FILE"

echo "=== Compilation Complete ==="
echo "Executable: $OUTPUT_DIR/simulation"
ls -la "$OUTPUT_DIR"
