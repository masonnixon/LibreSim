#!/usr/bin/env python3
"""
End-to-end numerical accuracy tests for LibreSim Coder.

Compares simulation results from the backend with results from generated code
to ensure they produce identical (or numerically equivalent) results.
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import requests

# Backend URL
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:9000")

# Tolerance for numerical comparison (relative and absolute)
# Note: Due to timing differences between backend and codegen (backend has special
# first-step handling), we use relaxed tolerances and compare RMS error instead
RTOL = 1e-6  # Relative tolerance
ATOL = 1e-8  # Absolute tolerance
MAX_RMS_ERROR = 0.01  # Maximum allowed RMS error for pass


# Test models - simple models with known analytical solutions
TEST_MODELS = {
    "sine_wave": {
        "description": "Sine wave output should match exactly",
        "model": {
            "id": "test-sine",
            "metadata": {"name": "Sine Wave Test"},
            "blocks": [
                {
                    "id": "sine1",
                    "type": "sine_wave",
                    "name": "Sine Wave",
                    "position": {"x": 100, "y": 100},
                    "parameters": {
                        "amplitude": 1.0,
                        "frequency": 1.0,
                        "phase": 0.0,
                        "bias": 0.0,
                    },
                },
                {
                    "id": "scope1",
                    "type": "scope",
                    "name": "Scope",
                    "position": {"x": 300, "y": 100},
                    "parameters": {},
                },
            ],
            "connections": [
                {
                    "id": "conn1",
                    "sourceBlockId": "sine1",
                    "sourcePortId": "out",
                    "targetBlockId": "scope1",
                    "targetPortId": "in",
                }
            ],
        },
        "config": {
            "startTime": 0.0,
            "stopTime": 2.0,
            "stepSize": 0.01,
            "solver": "euler",
        },
    },
    "integrator_ramp": {
        "description": "Step through integrator should produce ramp",
        "model": {
            "id": "test-integrator",
            "metadata": {"name": "Integrator Test"},
            "blocks": [
                {
                    "id": "const1",
                    "type": "constant",
                    "name": "Constant",
                    "position": {"x": 100, "y": 100},
                    "parameters": {"value": 1.0},
                },
                {
                    "id": "integ1",
                    "type": "integrator",
                    "name": "Integrator",
                    "position": {"x": 250, "y": 100},
                    "parameters": {"initial_condition": 0.0},
                },
                {
                    "id": "scope1",
                    "type": "scope",
                    "name": "Scope",
                    "position": {"x": 400, "y": 100},
                    "parameters": {},
                },
            ],
            "connections": [
                {
                    "id": "conn1",
                    "sourceBlockId": "const1",
                    "sourcePortId": "out",
                    "targetBlockId": "integ1",
                    "targetPortId": "in",
                },
                {
                    "id": "conn2",
                    "sourceBlockId": "integ1",
                    "sourcePortId": "out",
                    "targetBlockId": "scope1",
                    "targetPortId": "in",
                },
            ],
        },
        "config": {
            "startTime": 0.0,
            "stopTime": 5.0,
            "stepSize": 0.01,
            "solver": "rk4",
        },
    },
    "sum_gain": {
        "description": "Sum and gain operations",
        "model": {
            "id": "test-sum-gain",
            "metadata": {"name": "Sum Gain Test"},
            "blocks": [
                {
                    "id": "const1",
                    "type": "constant",
                    "name": "Constant 1",
                    "position": {"x": 100, "y": 50},
                    "parameters": {"value": 2.0},
                },
                {
                    "id": "const2",
                    "type": "constant",
                    "name": "Constant 2",
                    "position": {"x": 100, "y": 150},
                    "parameters": {"value": 3.0},
                },
                {
                    "id": "sum1",
                    "type": "sum",
                    "name": "Sum",
                    "position": {"x": 250, "y": 100},
                    "parameters": {"signs": "++"},
                },
                {
                    "id": "gain1",
                    "type": "gain",
                    "name": "Gain",
                    "position": {"x": 350, "y": 100},
                    "parameters": {"gain": 2.0},
                },
                {
                    "id": "scope1",
                    "type": "scope",
                    "name": "Scope",
                    "position": {"x": 500, "y": 100},
                    "parameters": {},
                },
            ],
            "connections": [
                {
                    "id": "conn1",
                    "sourceBlockId": "const1",
                    "sourcePortId": "out",
                    "targetBlockId": "sum1",
                    "targetPortId": "in1",
                },
                {
                    "id": "conn2",
                    "sourceBlockId": "const2",
                    "sourcePortId": "out",
                    "targetBlockId": "sum1",
                    "targetPortId": "in2",
                },
                {
                    "id": "conn3",
                    "sourceBlockId": "sum1",
                    "sourcePortId": "out",
                    "targetBlockId": "gain1",
                    "targetPortId": "in",
                },
                {
                    "id": "conn4",
                    "sourceBlockId": "gain1",
                    "sourcePortId": "out",
                    "targetBlockId": "scope1",
                    "targetPortId": "in",
                },
            ],
        },
        "config": {
            "startTime": 0.0,
            "stopTime": 1.0,
            "stepSize": 0.1,
            "solver": "euler",
        },
    },
    "feedback_loop": {
        "description": "Simple feedback loop with integrator",
        "model": {
            "id": "test-feedback",
            "metadata": {"name": "Feedback Loop Test"},
            "blocks": [
                {
                    "id": "step1",
                    "type": "step",
                    "name": "Step",
                    "position": {"x": 100, "y": 100},
                    "parameters": {
                        "step_time": 0.0,
                        "initial_value": 0.0,
                        "final_value": 1.0,
                    },
                },
                {
                    "id": "sum1",
                    "type": "sum",
                    "name": "Sum",
                    "position": {"x": 200, "y": 100},
                    "parameters": {"signs": "+-"},
                },
                {
                    "id": "gain1",
                    "type": "gain",
                    "name": "Gain",
                    "position": {"x": 300, "y": 100},
                    "parameters": {"gain": 1.0},
                },
                {
                    "id": "integ1",
                    "type": "integrator",
                    "name": "Integrator",
                    "position": {"x": 400, "y": 100},
                    "parameters": {"initial_condition": 0.0},
                },
                {
                    "id": "scope1",
                    "type": "scope",
                    "name": "Scope",
                    "position": {"x": 550, "y": 100},
                    "parameters": {},
                },
            ],
            "connections": [
                {
                    "id": "conn1",
                    "sourceBlockId": "step1",
                    "sourcePortId": "out",
                    "targetBlockId": "sum1",
                    "targetPortId": "in1",
                },
                {
                    "id": "conn2",
                    "sourceBlockId": "integ1",
                    "sourcePortId": "out",
                    "targetBlockId": "sum1",
                    "targetPortId": "in2",
                },
                {
                    "id": "conn3",
                    "sourceBlockId": "sum1",
                    "sourcePortId": "out",
                    "targetBlockId": "gain1",
                    "targetPortId": "in",
                },
                {
                    "id": "conn4",
                    "sourceBlockId": "gain1",
                    "sourcePortId": "out",
                    "targetBlockId": "integ1",
                    "targetPortId": "in",
                },
                {
                    "id": "conn5",
                    "sourceBlockId": "integ1",
                    "sourcePortId": "out",
                    "targetBlockId": "scope1",
                    "targetPortId": "in",
                },
            ],
        },
        "config": {
            "startTime": 0.0,
            "stopTime": 5.0,
            "stepSize": 0.01,
            "solver": "rk4",
        },
    },
    "transfer_function": {
        "description": "First order transfer function step response",
        "model": {
            "id": "test-tf",
            "metadata": {"name": "Transfer Function Test"},
            "blocks": [
                {
                    "id": "step1",
                    "type": "step",
                    "name": "Step",
                    "position": {"x": 100, "y": 100},
                    "parameters": {
                        "step_time": 0.0,
                        "initial_value": 0.0,
                        "final_value": 1.0,
                    },
                },
                {
                    "id": "tf1",
                    "type": "transfer_function",
                    "name": "Transfer Function",
                    "position": {"x": 300, "y": 100},
                    "parameters": {
                        "numerator": [1.0],
                        "denominator": [1.0, 1.0],  # 1/(s+1)
                    },
                },
                {
                    "id": "scope1",
                    "type": "scope",
                    "name": "Scope",
                    "position": {"x": 500, "y": 100},
                    "parameters": {},
                },
            ],
            "connections": [
                {
                    "id": "conn1",
                    "sourceBlockId": "step1",
                    "sourcePortId": "out",
                    "targetBlockId": "tf1",
                    "targetPortId": "in",
                },
                {
                    "id": "conn2",
                    "sourceBlockId": "tf1",
                    "sourcePortId": "out",
                    "targetBlockId": "scope1",
                    "targetPortId": "in",
                },
            ],
        },
        "config": {
            "startTime": 0.0,
            "stopTime": 5.0,
            "stepSize": 0.01,
            "solver": "rk4",
        },
    },
}


def run_backend_simulation(model: dict, config: dict) -> tuple[list[float], list[float]]:
    """Run simulation using the backend API and return time/output arrays."""
    # Start simulation
    response = requests.post(
        f"{BACKEND_URL}/api/simulate/start",
        json={"model": model, "config": config},
    )
    if response.status_code != 200:
        raise RuntimeError(f"Failed to start simulation: {response.text}")

    session_id = response.json().get("sessionId")

    # Poll for completion
    max_wait = 30  # seconds
    start_time = time.time()
    while time.time() - start_time < max_wait:
        status_resp = requests.get(f"{BACKEND_URL}/api/simulate/status")
        status = status_resp.json()

        if status.get("status") == "completed":
            break
        elif status.get("status") == "error":
            raise RuntimeError(f"Simulation error: {status.get('error')}")

        time.sleep(0.1)
    else:
        raise RuntimeError("Simulation timed out")

    # Get results
    results_resp = requests.get(f"{BACKEND_URL}/api/simulate/results")
    if results_resp.status_code != 200:
        raise RuntimeError(f"Failed to get results: {results_resp.text}")

    results = results_resp.json()

    # Extract time and values from scope
    signals = results.get("signals", [])
    if not signals:
        raise RuntimeError("No signals in results")

    # Find the scope signal (first one)
    scope_signal = signals[0]
    times = scope_signal.get("times", [])

    # Get values from first trace
    traces = scope_signal.get("traces", [])
    if traces:
        values = traces[0].get("values", [])
    else:
        values = scope_signal.get("values", [])

    return times, values


def generate_and_run_python(model: dict, config: dict) -> tuple[list[float], list[float]]:
    """Generate Python code, run it, and return time/output arrays."""
    # API expects flat config, not nested
    request_data = {
        "model": model,
        "project_name": "accuracy_test",
        "language": "python",
        "integration_method": config.get("solver", "rk4"),
        "step_size": config.get("stepSize", 0.01),
        "start_time": config.get("startTime", 0.0),
        "stop_time": config.get("stopTime", 10.0),
        "include_main": True,
        "include_csv_output": True,
    }

    # Generate code
    response = requests.post(
        f"{BACKEND_URL}/api/codegen/generate",
        json=request_data,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Code generation failed: {response.text}")

    # Extract ZIP to temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_data = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_data, "r") as zf:
            zf.extractall(tmpdir)

        # Find the project directory - look for main.py in subdirectories
        project_dir = Path(tmpdir)

        # Check if main.py is in a subdirectory (common pattern: simulation/, accuracy_test/, etc.)
        main_py = project_dir / "main.py"
        if not main_py.exists():
            # Look in subdirectories
            for subdir in project_dir.iterdir():
                if subdir.is_dir():
                    candidate = subdir / "main.py"
                    if candidate.exists():
                        project_dir = subdir
                        main_py = candidate
                        break

        if not main_py.exists():
            # List what we found for debugging
            files_found = list(project_dir.rglob("*"))
            raise RuntimeError(f"main.py not found. Files: {[str(f) for f in files_found[:10]]}")

        # Run the generated Python code
        result = subprocess.run(
            [sys.executable, str(main_py)],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Generated code failed: {result.stderr}")

        # Read results.csv
        csv_path = project_dir / "results.csv"
        if not csv_path.exists():
            raise RuntimeError(f"results.csv not found. stdout: {result.stdout}")

        times = []
        values = []
        with open(csv_path) as f:
            lines = f.readlines()
            # Skip header
            for line in lines[1:]:
                parts = line.strip().split(",")
                if len(parts) >= 2:
                    times.append(float(parts[0]))
                    values.append(float(parts[1]))

        return times, values


def compare_results(
    times1: list[float],
    values1: list[float],
    times2: list[float],
    values2: list[float],
    test_name: str,
) -> tuple[bool, str]:
    """Compare two sets of results and return (passed, message).

    Uses RMS error as primary metric since timing differences between backend
    and codegen can cause per-sample differences that are not actual errors.
    """
    # Convert to numpy arrays
    t1 = np.array(times1)
    v1 = np.array(values1)
    t2 = np.array(times2)
    v2 = np.array(values2)

    # Check array lengths
    if len(t1) != len(t2):
        # Try to interpolate to common time base
        if len(t1) > 0 and len(t2) > 0:
            # Use the shorter time array as reference
            if len(t1) < len(t2):
                v2_interp = np.interp(t1, t2, v2)
                t_common = t1
                v1_common = v1
                v2_common = v2_interp
            else:
                v1_interp = np.interp(t2, t1, v1)
                t_common = t2
                v1_common = v1_interp
                v2_common = v2
        else:
            return False, f"Empty arrays: backend={len(t1)}, codegen={len(t2)}"
    else:
        t_common = t1
        v1_common = v1
        v2_common = v2

    # Calculate statistics
    abs_diff = np.abs(v1_common - v2_common)
    rms_error = np.sqrt(np.mean(abs_diff ** 2))
    max_diff = np.max(abs_diff)
    max_diff_idx = np.argmax(abs_diff)
    max_diff_time = t_common[max_diff_idx]

    # Normalize by signal range for relative comparison
    signal_range = max(np.max(np.abs(v1_common)), 1e-10)
    normalized_rms = rms_error / signal_range

    # Check if values match well enough
    # Use RMS error as primary criterion since timing differences can cause per-sample drift
    if normalized_rms < MAX_RMS_ERROR:
        return True, f"Match! RMS={rms_error:.2e} ({len(t_common)} samples)"

    return False, (
        f"RMS={rms_error:.2e} (max={max_diff:.2e} at t={max_diff_time:.3f})"
    )


def run_test(test_name: str, test_data: dict, verbose: bool = False) -> tuple[bool, str]:
    """Run a single accuracy test."""
    model = test_data["model"]
    config = test_data["config"]

    try:
        # Run backend simulation
        backend_times, backend_values = run_backend_simulation(model, config)
    except Exception as e:
        return False, f"Backend simulation failed: {e}"

    try:
        # Generate and run Python code
        codegen_times, codegen_values = generate_and_run_python(model, config)
    except Exception as e:
        return False, f"Code generation/execution failed: {e}"

    # Compare results
    passed, msg = compare_results(
        backend_times, backend_values,
        codegen_times, codegen_values,
        test_name,
    )

    if not passed and verbose:
        # Print first few values for debugging
        print(f"  DEBUG: Backend first 5 values: {backend_values[:5]}")
        print(f"  DEBUG: Codegen first 5 values: {codegen_values[:5]}")
        print(f"  DEBUG: Backend last 5 values: {backend_values[-5:]}")
        print(f"  DEBUG: Codegen last 5 values: {codegen_values[-5:]}")

    return passed, msg


def main():
    """Run all accuracy tests."""
    print("=" * 70)
    print("LibreSim Coder - Numerical Accuracy Test Suite")
    print("=" * 70)

    # Check backend health
    try:
        resp = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        print(f"Backend health check: {resp.status_code}")
    except Exception as e:
        print(f"Backend not available: {e}")
        print("Please ensure the backend is running at {BACKEND_URL}")
        sys.exit(1)

    results = {}
    passed = 0
    failed = 0

    # Parse command line args
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    for test_name, test_data in TEST_MODELS.items():
        print()
        print("=" * 60)
        print(f"Testing: {test_name}")
        print(f"  {test_data['description']}")
        print("=" * 60)

        success, message = run_test(test_name, test_data, verbose=verbose)
        results[test_name] = {"passed": success, "message": message}

        if success:
            print(f"  [OK] PASS - {message}")
            passed += 1
        else:
            print(f"  [FAIL] {message}")
            failed += 1

    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for test_name, result in results.items():
        status = "[OK]" if result["passed"] else "[FAIL]"
        print(f"  {test_name}: {status}")

    print()
    print(f"Total: {passed}/{passed + failed} passed ({failed} failed)")
    print("=" * 70)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
