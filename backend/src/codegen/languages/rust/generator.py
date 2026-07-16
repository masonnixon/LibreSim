"""Rust code generator."""

from typing import Any

from ...integration import IntegrationCodeGenerator
from ...models import (
    BlockInfo,
    CompiledModelInfo,
    GeneratedProject,
    IntegrationMethod,
    Language,
)
from ..base import LanguageGenerator
from .blocks import get_block_template


class RustCodeGenerator(LanguageGenerator):
    """Generate Rust simulation code."""

    def generate(
        self,
        model_info: CompiledModelInfo,
        config: Any,
    ) -> GeneratedProject:
        """Generate a complete Rust project."""
        project = GeneratedProject(
            name=config.project_name,
            language=Language.RUST,
        )

        # Generate source files
        project.add_file("src/lib.rs", self._generate_lib(model_info, config))
        project.add_file("src/blocks.rs", self._generate_blocks(model_info))
        project.add_file("src/integration.rs", IntegrationCodeGenerator.generate_rust())

        # Generate main.rs
        if config.include_main:
            project.add_file("src/main.rs", self.generate_main_code(model_info, config))

        # Generate build files
        project.add_file("Cargo.toml", self._generate_cargo(config))
        project.add_file("README.md", self._generate_readme(model_info, config))

        # Generate Dockerfile and build/run scripts
        project.add_file("Dockerfile", self._generate_dockerfile(config))
        project.add_file("build.sh", self._generate_build_script(config))
        project.add_file("run.sh", self._generate_run_script(config))

        return project

    def generate_block_code(self, block: BlockInfo) -> str:
        """Generate code for a single block."""
        template = get_block_template(block.type)
        struct_name = f"Block_{self.sanitize_identifier(block.id)}"

        if template is None:
            return self._generate_passthrough_block(block, struct_name)

        return template(block, struct_name)

    def generate_integration_code(self, method: IntegrationMethod) -> str:
        """Generate integration method code."""
        return IntegrationCodeGenerator.generate_rust()

    def _generate_output_recording(self, model_info: CompiledModelInfo) -> dict:
        """Generate output recording code from the shared canonical output schema."""
        output_names: list[str] = []
        record_code_lines: list[str] = []
        blocks = {block.id: block for block in model_info.blocks}

        for signal in model_info.output_signals:
            source = blocks[signal.source_block_id]
            var_name = f"block_{self.sanitize_identifier(source.id)}"
            port = signal.flat_index if signal.dimensions[0] > 1 else signal.source_output_port
            output_names.append(signal.canonical_key)
            record_code_lines.append(
                f"                output_data.push(model.{var_name}.get_output({port}));"
            )

        return {
            "names": output_names,
            "n_outputs": len(output_names),
            "record_code": "\n".join(record_code_lines)
            if record_code_lines
            else "                // No outputs to record",
        }

    def generate_main_code(
        self,
        model_info: CompiledModelInfo,
        config: Any,
    ) -> str:
        """Generate main entry point code."""
        project_name = config.project_name.replace("-", "_")
        # Rust package names cannot start with a digit - prefix with underscore if needed
        if project_name and project_name[0].isdigit():
            project_name = "_" + project_name

        # Get output recording info
        output_info = self._generate_output_recording(model_info)
        actual_n_outputs = output_info["n_outputs"]
        n_outputs = actual_n_outputs or 1  # Use 1 for array sizing if no outputs
        output_names = output_info["names"]
        record_code = output_info["record_code"]

        # Build CSV header with column names
        csv_header_parts = ["time"] + output_names
        csv_header = ",".join(csv_header_parts)

        csv_code = ""
        # Only generate CSV code if there are actual outputs to record
        if config.include_csv_output and actual_n_outputs > 0:
            # Build write format string and args for all outputs
            format_parts = ["{:.6}"]  # time
            for _i in range(n_outputs):
                format_parts.append(",{:.6}")
            format_string = "".join(format_parts)

            write_args = ["t"]
            for idx in range(n_outputs):
                write_args.append(f"output_data[i * {n_outputs} + {idx}]")
            write_args_str = ", ".join(write_args)

            csv_code = f"""
    // Write results to CSV
    let mut csv_file = std::fs::File::create("results.csv").expect("Could not create file");
    use std::io::Write;
    writeln!(csv_file, "{csv_header}").unwrap();
    let n_outputs = {n_outputs};
    for i in 0..time_data.len() {{
        let t = time_data[i];
        writeln!(csv_file, "{format_string}", {write_args_str}).unwrap();
    }}
    println!("Results written to results.csv");
"""
        elif config.include_csv_output:
            # No outputs - write time-only CSV
            csv_code = """
    // Write results to CSV (time only - no output signals)
    let mut csv_file = std::fs::File::create("results.csv").expect("Could not create file");
    use std::io::Write;
    writeln!(csv_file, "time").unwrap();
    for i in 0..time_data.len() {
        let t = time_data[i];
        writeln!(csv_file, "{:.6}", t).unwrap();
    }
    println!("Results written to results.csv");
"""

        return f"""//! Example simulation runner
//! Generated by LibreSim Coder.

use {project_name}::Model;
use {project_name}::integration::{{IntegrationMethod, get_num_passes, get_stage_offsets}};

fn main() {{
    let mut model = Model::new();
    model.init();

    let mut t = {config.start_time}_f64;
    let dt = {config.step_size}_f64;
    let t_end = {config.stop_time}_f64;

    // Allocate output storage
    let n_samples = ((t_end - t) / dt) as usize + 2;
    let n_outputs = {n_outputs};  // Number of output signals
    let mut time_data: Vec<f64> = Vec::with_capacity(n_samples);
    let mut output_data: Vec<f64> = Vec::with_capacity(n_samples * n_outputs);

    println!("Running simulation...");

    let method = IntegrationMethod::from_str("{config.integration_method.value}");
    let num_passes = get_num_passes(method);
    let stage_offsets = get_stage_offsets(method);

    while t <= t_end {{
        // Major-step update: commit sampled state and establish recorded outputs.
        model.step(t, dt, 0, true);
        time_data.push(t);
{record_code}

        // Integration passes
        for kpass in 0..num_passes {{
            model.step(t + stage_offsets[kpass] * dt, dt, kpass, false);

            model.propagate_integrators(dt, kpass, method);
        }}

        t += dt;
    }}

    println!("Simulation complete. {{}} samples.", time_data.len());
{csv_code}
}}
"""

    def _generate_lib(self, model_info: CompiledModelInfo, config: Any) -> str:
        """Generate lib.rs with Model struct."""
        # Build block member declarations
        block_members = []
        for block in model_info.blocks:
            struct_name = f"Block_{self.sanitize_identifier(block.id)}"
            var_name = f"block_{self.sanitize_identifier(block.id)}"
            block_members.append(f"    pub {var_name}: blocks::{struct_name},")

        # Build initialization calls
        init_calls = []
        for block in model_info.blocks:
            var_name = f"block_{self.sanitize_identifier(block.id)}"
            init_calls.append(f"        self.{var_name}.init();")

        # Build per-block wiring for inline wiring during step
        block_wiring = self._generate_per_block_wiring(model_info)

        # Build update calls in execution order with inline wiring
        update_calls: list[str] = []
        for block_id in model_info.execution_order:
            block_match = next((b for b in model_info.blocks if b.id == block_id), None)
            if block_match is not None:
                var_name = f"block_{self.sanitize_identifier(block_match.id)}"
                # Add wiring for this block's inputs (if any)
                if block_id in block_wiring:
                    for wire_line in block_wiring[block_id]:
                        update_calls.append(wire_line)
                if block_match.ready_only:
                    update_calls.append(f"        if ready {{ self.{var_name}.update(t); }}")
                elif block_match.type in {
                    "rate_limiter",
                    "madgwick_filter",
                    "complementary_filter",
                }:
                    update_calls.append(f"        self.{var_name}.update(t, dt);")
                else:
                    update_calls.append(f"        self.{var_name}.update(t);")

        # Build connection wiring (for wire_connections method - kept for compatibility)
        connection_code = self._generate_connection_code(model_info)

        # Build output getter
        output_code = "        0.0"
        if model_info.sink_blocks:
            first_sink_id = model_info.sink_blocks[0]
            sink_block = next((b for b in model_info.blocks if b.id == first_sink_id), None)
            if sink_block:
                var_name = f"block_{self.sanitize_identifier(sink_block.id)}"
                output_code = f"        self.{var_name}.get_output(port)"

        # Build integrator propagation
        integrator_code = self._generate_integrator_propagation(model_info)

        # Build default implementation
        default_fields = []
        for block in model_info.blocks:
            struct_name = f"Block_{self.sanitize_identifier(block.id)}"
            var_name = f"block_{self.sanitize_identifier(block.id)}"
            default_fields.append(f"            {var_name}: blocks::{struct_name}::new(),")

        return f"""//! Simulation library
//! Generated by LibreSim Coder.

pub mod blocks;
pub mod integration;

use integration::IntegrationMethod;

/// Model containing all simulation blocks.
#[derive(Clone)]
pub struct Model {{
    pub time: f64,
{chr(10).join(block_members)}
}}

impl Model {{
    /// Create a new model
    pub fn new() -> Self {{
        Self {{
            time: 0.0,
{chr(10).join(default_fields)}
        }}
    }}

    /// Initialize the model
    pub fn init(&mut self) {{
        self.time = 0.0;
{chr(10).join(init_calls)}
    }}

    /// Wire block connections (update inputs from outputs)
    pub fn wire_connections(&mut self) {{
{connection_code}
    }}

    /// Execute one simulation step
    pub fn step(&mut self, t: f64, dt: f64, _kpass: usize, ready: bool) {{
        self.time = t;

        // Update all blocks in execution order (with inline wiring)
{chr(10).join(update_calls)}
    }}

    /// Get model output
    pub fn get_output(&self, port: usize) -> f64 {{
{output_code}
    }}

    /// Propagate integrators using specified method
    pub fn propagate_integrators(&mut self, dt: f64, kpass: usize, method: IntegrationMethod) {{
{integrator_code}
    }}
}}

impl Default for Model {{
    fn default() -> Self {{
        Self::new()
    }}
}}
"""

    def _generate_per_block_wiring(self, model_info: CompiledModelInfo) -> dict:
        """Generate per-block wiring code for inline wiring during step.

        Returns:
            Dictionary mapping block_id to list of wiring code lines
        """
        wiring: dict[str, list[str]] = {}
        for block in model_info.blocks:
            var_name = f"block_{self.sanitize_identifier(block.id)}"
            block_lines = []
            for conn in block.input_connections:
                source_id, source_port, target_port = self.parse_connection(conn)
                source_block = next((b for b in model_info.blocks if b.id == source_id), None)
                if source_block:
                    source_var = f"block_{self.sanitize_identifier(source_block.id)}"
                    port_idx = target_port if target_port is not None else 0

                    # Check if this is a vector-to-vector connection
                    source_is_vector = self._is_vector_output(source_block, source_port)
                    target_expects_vector = self._expects_vector_input(block, port_idx)

                    # Multi-input blocks use input0, input1, etc.
                    if block.type in self.MULTI_INPUT_BLOCKS:
                        block_lines.append(
                            f"        self.{var_name}.input{port_idx} = "
                            f"self.{source_var}.get_output({source_port});"
                        )
                    elif source_is_vector and target_expects_vector:
                        # Vector-to-vector: clone the array
                        input_field = "input" if port_idx == 0 else f"input{port_idx}"
                        # For demux outputs, use port-specific get_output_vector{n}
                        vector_suffix = "" if source_port == 0 else str(source_port)
                        block_lines.append(
                            f"        self.{var_name}.{input_field} = "
                            f"*self.{source_var}.get_output_vector{vector_suffix}();"
                        )
                    elif target_port is not None and target_port > 0:
                        block_lines.append(
                            f"        self.{var_name}.input{target_port} = "
                            f"self.{source_var}.get_output({source_port});"
                        )
                    else:
                        block_lines.append(
                            f"        self.{var_name}.input = "
                            f"self.{source_var}.get_output({source_port});"
                        )
            if block_lines:
                wiring[block.id] = block_lines
        return wiring

    def _generate_blocks(self, model_info: CompiledModelInfo) -> str:
        """Generate blocks.rs with all block struct definitions."""
        header = """//! Block definitions
//! Generated by LibreSim Coder.

#![allow(dead_code)]
#![allow(clippy::needless_return)]

use crate::integration::{IntegrationMethod, propagate_integrator};

"""
        # Generate struct declarations for each block
        structs = []
        for block in model_info.blocks:
            struct_code = self.generate_block_code(block)
            structs.append(struct_code)

        return header + "\n".join(structs)

    # Block types that use indexed inputs (input0, input1, etc.)
    MULTI_INPUT_BLOCKS = {"sum", "product", "mux", "switch"}

    # Block types that output vectors and have get_output_vector() method
    VECTOR_OUTPUT_BLOCKS = {"mux", "constant", "gain", "demux"}

    # Block types that expect vector inputs (not via indexed ports)
    VECTOR_INPUT_BLOCKS = {"demux", "gain"}

    def _is_vector_output(self, block: "BlockInfo", port: int = 0) -> bool:
        """Check if a block's output port produces a vector (not scalar)."""
        if block.output_dimensions and port < len(block.output_dimensions):
            dims = block.output_dimensions[port]
            if len(dims) > 0 and dims[0] > 1:
                return True
        if block.type in self.VECTOR_OUTPUT_BLOCKS:
            if block.type == "mux":
                return True
            if block.type == "constant":
                value = block.parameters.get("value", 0.0)
                return isinstance(value, (list, tuple))
        return False

    def _expects_vector_input(self, block: "BlockInfo", port: int = 0) -> bool:
        """Check if a block expects a vector input (not scalar) at given port."""
        if block.input_dimensions and port < len(block.input_dimensions):
            dims = block.input_dimensions[port]
            if len(dims) > 0 and dims[0] > 1:
                return True
        if block.type == "demux":
            return True
        return False

    def _generate_connection_code(self, model_info: CompiledModelInfo) -> str:
        """Generate connection wiring code."""
        lines = []
        for block in model_info.blocks:
            var_name = f"block_{self.sanitize_identifier(block.id)}"
            for conn in block.input_connections:
                source_id, source_port, target_port = self.parse_connection(conn)
                source_block = next((b for b in model_info.blocks if b.id == source_id), None)
                if source_block:
                    source_var = f"block_{self.sanitize_identifier(source_block.id)}"
                    port_idx = target_port if target_port is not None else 0

                    # Check if this is a vector-to-vector connection
                    source_is_vector = self._is_vector_output(source_block, source_port)
                    target_expects_vector = self._expects_vector_input(block, port_idx)

                    # Multi-input blocks use input0, input1, etc.
                    if block.type in self.MULTI_INPUT_BLOCKS:
                        lines.append(
                            f"        self.{var_name}.input{port_idx} = "
                            f"self.{source_var}.get_output({source_port});"
                        )
                    elif source_is_vector and target_expects_vector:
                        # Vector-to-vector: clone the array
                        # For port 0 use 'input', for port 1+ use 'input1', 'input2', etc.
                        input_field = "input" if port_idx == 0 else f"input{port_idx}"
                        lines.append(
                            f"        self.{var_name}.{input_field} = "
                            f"self.{source_var}.get_output_vector().clone();"
                        )
                    elif target_port is not None and target_port > 0:
                        lines.append(
                            f"        self.{var_name}.input{target_port} = "
                            f"self.{source_var}.get_output({source_port});"
                        )
                    else:
                        lines.append(
                            f"        self.{var_name}.input = "
                            f"self.{source_var}.get_output({source_port});"
                        )

        return "\n".join(lines) if lines else "        // No connections"

    def _generate_integrator_propagation(self, model_info: CompiledModelInfo) -> str:
        """Generate integrator propagation code for RK methods."""
        lines = []
        integrator_ids = set(model_info.integrator_blocks)
        for block in model_info.blocks:
            if block.id in integrator_ids or block.custom_state_propagation:
                var_name = f"block_{self.sanitize_identifier(block.id)}"
                if block.type == "integrator":
                    # Get derivative first to avoid borrow conflicts
                    lines.append(f"""        // Integrator: {block.name}
        let deriv_{self.sanitize_identifier(block.id)} = self.{var_name}.get_derivative();
        integration::propagate_integrator(
            &mut self.{var_name}.state,
            &mut self.{var_name}.x0,
            &mut self.{var_name}.xd0,
            &mut self.{var_name}.xd1,
            &mut self.{var_name}.xd2,
            &mut self.{var_name}.xd3,
            deriv_{self.sanitize_identifier(block.id)},
            dt, kpass, method
        );""")
                elif block.custom_state_propagation:
                    lines.append(f"""        // {block.type}: {block.name}
        self.{var_name}.propagate_states(dt, kpass, method);""")

        return "\n".join(lines) if lines else "        // No integrators to propagate"

    def _generate_passthrough_block(self, block: BlockInfo, struct_name: str) -> str:
        """Generate a passthrough block for unsupported types."""
        # Determine number of inputs from connections
        num_inputs = 1
        for conn in block.input_connections:
            _, _, target_port = self.parse_connection(conn)
            if target_port is not None:
                num_inputs = max(num_inputs, target_port + 1)

        # Generate input declarations
        input_decls = []
        for i in range(num_inputs):
            if i == 0:
                input_decls.append("    pub input: f64,")
            else:
                input_decls.append(f"    pub input{i}: f64,")
        input_decls_str = "\n".join(input_decls)

        # Generate new() initializers
        new_inits = []
        for i in range(num_inputs):
            if i == 0:
                new_inits.append("            input: 0.0,")
            else:
                new_inits.append(f"            input{i}: 0.0,")
        new_inits_str = "\n".join(new_inits)

        return f"""
/// {block.name} - Passthrough (type: {block.type})
#[derive(Clone, Default)]
pub struct {struct_name} {{
{input_decls_str}
    pub output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
{new_inits_str}
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = self.input;  // Uses first input as passthrough
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""

    def _generate_cargo(self, config: Any) -> str:
        """Generate Cargo.toml."""
        project_name = config.project_name.replace("-", "_")
        # Rust package names cannot start with a digit - prefix with underscore if needed
        if project_name and project_name[0].isdigit():
            project_name = "_" + project_name
        return f"""[package]
name = "{project_name}"
version = "0.1.0"
edition = "2021"
description = "Simulation generated by LibreSim Coder"

[dependencies]

[[bin]]
name = "simulation"
path = "src/main.rs"

[lib]
name = "{project_name}"
path = "src/lib.rs"

[profile.release]
opt-level = 3
lto = true
"""

    def _generate_readme(self, model_info: CompiledModelInfo, config: Any) -> str:
        """Generate README.md."""
        return f"""# {config.project_name}

Rust simulation generated by LibreSim Coder.

## Quick Start

```bash
# Build in release mode
cargo build --release

# Run the simulation
cargo run --release
```

## Model Information

- **Blocks**: {len(model_info.blocks)}
- **Integration Method**: {config.integration_method.value}
- **Step Size**: {config.step_size}
- **Duration**: {config.start_time} to {config.stop_time} seconds

## Files

- `src/lib.rs` - Model struct and simulation logic
- `src/blocks.rs` - Block struct definitions
- `src/integration.rs` - Numerical integration methods
- `src/main.rs` - Example runner (outputs to results.csv)

## Customization

To modify simulation parameters, edit the constants in `main.rs`:

```rust
let mut t = {config.start_time}_f64;      // Start time
let dt = {config.step_size}_f64;          // Step size
let t_end = {config.stop_time}_f64;       // End time
```

## Performance

The generated code uses Rust's zero-cost abstractions and is compiled
with full optimizations in release mode. For best performance, always
use `cargo run --release` or `cargo build --release`.

## Docker Build

To create a standalone executable using Docker:

```bash
# Build using the provided script
./build.sh

# Or manually:
docker build -t {config.project_name}-builder .
docker run --rm -v $(pwd)/output:/output {config.project_name}-builder
```

The executable will be created in the `output/` directory.
"""

    def _generate_dockerfile(self, config: Any) -> str:
        """Generate Dockerfile for compilation and execution."""
        return f"""# Dockerfile for compiling and running {config.project_name}
# Generated by LibreSim Coder

FROM rust:1.75-bookworm

LABEL maintainer="LibreSim Coder"
LABEL description="Build environment for {config.project_name}"

# Set working directory
WORKDIR /build

# Copy project files
COPY . /build/

# Make scripts executable
RUN chmod +x /build/run.sh

# Build the project in release mode
RUN cargo build --release

# Default command runs the simulation and copies outputs
CMD ["/build/run.sh"]
"""

    def _generate_build_script(self, config: Any) -> str:
        """Generate build script."""
        return f"""#!/bin/bash
# Build and run script for {config.project_name}
# Generated by LibreSim Coder
#
# This script:
# 1. Builds a Docker image with the compiled simulation
# 2. Runs the simulation inside the container
# 3. Copies the executable and results to ./output/

set -e

PROJECT_NAME="{config.project_name}"
IMAGE_NAME="${{PROJECT_NAME}}-builder"

echo "=== Building and Running $PROJECT_NAME (Rust) ==="

# Create output directory
mkdir -p output

# Get absolute path (works on both Linux/Mac and Windows Git Bash)
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ -n "$WINDIR" ]]; then
    # Windows: convert to Docker-compatible path
    OUTPUT_PATH="$(cd output && pwd -W 2>/dev/null || pwd)"
else
    OUTPUT_PATH="$(cd output && pwd)"
fi

# Build Docker image (compiles the code)
echo "[1/2] Building Docker image (compiling code)..."
docker build -t "$IMAGE_NAME" .

# Run container (executes simulation and copies outputs)
echo "[2/2] Running simulation..."
# MSYS_NO_PATHCONV prevents Git Bash from mangling the volume mount path
MSYS_NO_PATHCONV=1 docker run --rm -v "$OUTPUT_PATH:/output" "$IMAGE_NAME"

echo ""
echo "=== Complete ==="
echo "Output files:"
ls -la output/

# Show first/last few lines of results if CSV exists
if [ -f output/results.csv ]; then
    echo ""
    echo "=== Results Preview (first 5 lines) ==="
    head -n 5 output/results.csv
    echo "..."
    echo "=== Results Preview (last 5 lines) ==="
    tail -n 5 output/results.csv
fi
"""

    def _generate_run_script(self, config: Any) -> str:
        """Generate run script that executes inside Docker container."""
        return f"""#!/bin/bash
# Run script for {config.project_name}
# This script runs inside the Docker container
# Generated by LibreSim Coder

set -e

echo "Running simulation..."

# Run the simulation (generates results.csv in current directory)
cd /build/target/release
./simulation

echo ""
echo "Simulation complete."

# Copy outputs to mounted volume
if [ -d "/output" ]; then
    echo "Copying outputs to /output..."
    cp -f simulation /output/ 2>/dev/null || true
    cp -f results.csv /output/ 2>/dev/null || true
    echo "Done."
else
    echo "Warning: /output not mounted, results not copied."
fi
"""
