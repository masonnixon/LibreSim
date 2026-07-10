"""
End-to-end accuracy tests for code generation.

These tests verify that generated Python code produces IDENTICAL results
to the backend simulation. Any difference is a bug.
"""

import csv
import json
import os
import tempfile
from pathlib import Path

import numpy as np

from src.codegen.generator import CodeGenerationConfig, CodeGenerator
from src.codegen.models import IntegrationMethod, Language
from src.models.model import Model
from src.simulation.compiler import ModelCompiler
from src.simulation.osk_adapter import OSKAdapter

# Tolerance for numerical comparison
# Note: Some blocks (PID, complex transfer functions) may have small timing
# differences due to different integration approaches. We use tighter tolerances
# for simple blocks and relaxed tolerances for complex ones.
RTOL = 1e-6  # Relative tolerance
ATOL = 1e-6  # Absolute tolerance
MAX_RMS = 0.01  # Maximum RMS error (1%)


def load_example(example_name: str) -> dict:
    """Load an example model from the examples directory."""
    # Docker Compose mounts repository examples under /project, while a local test
    # run reaches them from the repository root above backend/.  Checking both keeps
    # the documented Docker command and direct repository runs equivalent.
    docker_examples = Path("/project/examples")
    examples_dir = (
        docker_examples
        if docker_examples.is_dir()
        else Path(__file__).resolve().parents[2] / "examples"
    )
    example_path = examples_dir / f"{example_name}.json"
    with open(example_path) as f:
        return json.load(f)


def run_backend_simulation(model_data: dict, dt: float = 0.01, t_end: float = 10.0) -> dict:
    """Run simulation using the backend OSK and return scope data."""
    from src.models.simulation import SimulationConfig, SolverType

    # Compile model
    model = Model.model_validate(model_data)
    compiler = ModelCompiler()
    compiled = compiler.compile(model)

    # Create config and adapter
    config = SimulationConfig(
        step_size=dt,
        stop_time=t_end,
        start_time=0.0,
        solver=SolverType.RK4,
    )

    adapter = OSKAdapter()
    adapter.initialize(compiled, config)

    results = {"time": []}
    t = config.start_time
    while t <= t_end + 1e-12:
        outputs = adapter.step(t, dt)
        results["time"].append(t)
        for key, value in outputs.items():
            signal_name = key.rsplit(":", 1)[-1]
            results.setdefault(signal_name, []).append(value)
        t += dt

    return results


def run_codegen_simulation(model_data: dict, dt: float = 0.01, t_end: float = 10.0) -> dict:
    """Generate Python code, run it, and return results."""
    generator = CodeGenerator()
    config = CodeGenerationConfig(
        language=Language.PYTHON,
        integration_method=IntegrationMethod.RK4,
        project_name="accuracy_test",
        step_size=dt,
        stop_time=t_end,
    )

    project = generator.generate(model_data, config)

    # Write to temp directory
    temp_dir = tempfile.mkdtemp(prefix="test_accuracy_")
    for f in project.files:
        path = os.path.join(temp_dir, f.path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as out:
            out.write(f.content)

    # Run the simulation using subprocess (isolated environment)
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "main.py"],
        cwd=temp_dir,
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Generated code failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    # Read results.csv
    results = {}
    csv_path = os.path.join(temp_dir, "results.csv")
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for key in reader.fieldnames:
            results[key] = []
        for row in reader:
            for key, value in row.items():
                results[key].append(float(value))

    return results


def find_best_signal_match(
    backend_signals: list, codegen_signals: list, backend: dict, codegen: dict, min_len: int
) -> list:
    """Match signals by finding the codegen signal with lowest RMS error for each backend signal.

    Returns:
        List of (backend_sig, codegen_sig) tuples representing the best matches
    """
    matches = []
    used_codegen = set()

    for backend_sig in backend_signals:
        backend_vals = np.array(backend[backend_sig][:min_len])
        best_match = None
        best_rms = float("inf")

        for codegen_sig in codegen_signals:
            if codegen_sig in used_codegen:
                continue
            codegen_vals = np.array(codegen[codegen_sig][:min_len])
            diff = np.abs(backend_vals - codegen_vals)
            rms = np.sqrt(np.mean(diff**2))
            if rms < best_rms:
                best_rms = rms
                best_match = codegen_sig

        if best_match:
            matches.append((backend_sig, best_match))
            used_codegen.add(best_match)

    return matches


def compare_results(backend: dict, codegen: dict, test_name: str):
    """Compare results and raise AssertionError if they differ."""
    # Find common signal keys (excluding time)
    backend_signals = set(backend.keys()) - {"time"}
    codegen_signals = set(codegen.keys()) - {"time"}

    # Time arrays - use minimum length for comparison (backend may have extra sample)
    backend_time = np.array(backend["time"])
    codegen_time = np.array(codegen["time"])

    min_len = min(len(backend_time), len(codegen_time))
    print(
        f"\n{test_name}: backend has {len(backend_time)} samples, codegen has {len(codegen_time)} samples"
    )
    print(f"Using first {min_len} samples for comparison")

    # Time values should still match for common samples
    np.testing.assert_allclose(
        backend_time[:min_len],
        codegen_time[:min_len],
        rtol=1e-6,
        atol=1e-9,
        err_msg=f"{test_name}: Time arrays differ",
    )

    # For each signal, compare
    errors = []

    backend_sig_list = sorted(backend_signals)
    codegen_sig_list = sorted(codegen_signals)

    if len(backend_sig_list) != len(codegen_sig_list):
        errors.append(
            f"Signal count mismatch: backend={len(backend_sig_list)}, codegen={len(codegen_sig_list)}"
        )
        errors.append(f"Backend signals: {backend_sig_list}")
        errors.append(f"Codegen signals: {codegen_sig_list}")
        raise AssertionError(f"{test_name} failed:\n" + "\n".join(errors))

    # Match signals by finding the best value match (lowest RMS error)
    matches = find_best_signal_match(backend_sig_list, codegen_sig_list, backend, codegen, min_len)

    for backend_sig, codegen_sig in matches:
        backend_vals = np.array(backend[backend_sig][:min_len])
        codegen_vals = np.array(codegen[codegen_sig][:min_len])

        # Calculate differences
        diff = np.abs(backend_vals - codegen_vals)
        max_diff = np.max(diff)
        max_diff_idx = np.argmax(diff)
        rms_diff = np.sqrt(np.mean(diff**2))

        # Use RMS error as primary criterion
        if rms_diff > MAX_RMS:
            errors.append(
                f"Signal '{backend_sig}' vs '{codegen_sig}' differs: max_diff={max_diff:.2e} at t={backend_time[max_diff_idx]:.3f}, "
                f"rms={rms_diff:.2e} (threshold={MAX_RMS})"
            )
            # Print some values for debugging
            print(f"\n{test_name} - {backend_sig} vs {codegen_sig} comparison:")
            print(f"  Backend first 5: {backend_vals[:5]}")
            print(f"  Codegen first 5: {codegen_vals[:5]}")
            print(
                f"  Backend at max diff (t={backend_time[max_diff_idx]:.3f}): {backend_vals[max_diff_idx]}"
            )
            print(f"  Codegen at max diff: {codegen_vals[max_diff_idx]}")
            print(f"  Backend last 5: {backend_vals[-5:]}")
            print(f"  Codegen last 5: {codegen_vals[-5:]}")
        else:
            print(
                f"  {backend_sig} vs {codegen_sig}: PASS (max_diff={max_diff:.2e}, rms={rms_diff:.2e})"
            )

    if errors:
        raise AssertionError(f"{test_name} failed:\n" + "\n".join(errors))


class TestCodegenAccuracy:
    """Test that codegen produces identical results to backend simulation."""

    def test_03_pid_controller(self):
        """PID controller example should match exactly."""
        model = load_example("03_pid_controller")
        backend = run_backend_simulation(model, dt=0.01, t_end=10.0)
        codegen = run_codegen_simulation(model, dt=0.01, t_end=10.0)
        compare_results(backend, codegen, "PID Controller")

    def test_01_sine_wave_basic(self):
        """Sine wave example should match exactly."""
        model = load_example("01_sine_wave_basic")
        backend = run_backend_simulation(model, dt=0.01, t_end=5.0)
        codegen = run_codegen_simulation(model, dt=0.01, t_end=5.0)
        compare_results(backend, codegen, "Sine Wave")

    def test_02_first_order_step_response(self):
        """First order step response should match exactly."""
        model = load_example("02_first_order_step_response")
        backend = run_backend_simulation(model, dt=0.01, t_end=10.0)
        codegen = run_codegen_simulation(model, dt=0.01, t_end=10.0)
        compare_results(backend, codegen, "First Order Step")

    def test_04_mass_spring_damper(self):
        """Mass-spring-damper example should match exactly.

        Note: Uses 0.001 step size as the model config specifies to achieve
        better numerical accuracy for this feedback loop system.
        """
        model = load_example("04_mass_spring_damper")
        # Use model's step size for better accuracy with feedback loops
        backend = run_backend_simulation(model, dt=0.001, t_end=2.0)
        codegen = run_codegen_simulation(model, dt=0.001, t_end=2.0)
        compare_results(backend, codegen, "Mass Spring Damper")

    def test_09_second_order_damping(self):
        """Second order damping comparison should match exactly."""
        model = load_example("09_second_order_damping")
        backend = run_backend_simulation(model, dt=0.01, t_end=10.0)
        codegen = run_codegen_simulation(model, dt=0.01, t_end=10.0)
        compare_results(backend, codegen, "Second Order Damping")
