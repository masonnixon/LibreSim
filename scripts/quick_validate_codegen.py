#!/usr/bin/env python3
"""
Quick validation of code generation - tests a representative subset of examples.

This script tests examples that cover the key functionality:
1. Basic signal generation (01_sine_wave)
2. Step response with integrator (02_first_order_step_response)
3. PID controller (03_pid_controller)
4. Mass-spring-damper (04_mass_spring_damper)
5. Second order damping (09_second_order_damping)

For each, it compares the final output values from generated code vs headless sim.
"""

import asyncio
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

# Add backend to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from src.codegen.validation import compare_final_values, read_results_csv
from src.models.model import Model
from src.models.simulation import SimulationConfig
from src.simulation.runner import SimulationRunner

EXAMPLES_DIR = REPO_ROOT / "examples"
CODEGEN_DIR = REPO_ROOT / "codegen_verification"

# Get all examples from examples directory
def get_all_examples():
    """Get all example names from the examples directory."""
    return sorted([p.stem for p in EXAMPLES_DIR.glob("*.json")])

KEY_EXAMPLES = get_all_examples()

LANGUAGES = ["python", "cpp", "c", "rust"]


async def run_headless_async(example_name: str) -> dict:
    """Run headless simulation and return final values."""
    example_path = EXAMPLES_DIR / f"{example_name}.json"
    with open(example_path) as f:
        model_data = json.load(f)

    model = Model.model_validate(model_data)

    # Extract simulation config from model if present
    sim_config = model_data.get("simulationConfig", {})
    step_size = sim_config.get("stepSize", 0.01)
    stop_time = sim_config.get("stopTime", 10.0)
    start_time = sim_config.get("startTime", 0.0)

    config = SimulationConfig(stop_time=stop_time, step_size=step_size, start_time=start_time)
    runner = SimulationRunner(model, config)
    await runner.run()

    # Get results after simulation completes
    results = runner.get_results()

    final_values = {}
    # Results structure:
    # {
    #   "signals": [
    #     { "blockId": "...", "name": "...", "times": [...], "values": [...] },
    #     ...
    #   ],
    #   "analyses": [...],
    #   "statistics": { ... }
    # }
    signals = results.get("signals", [])
    for signal in signals:
        name = signal.get("name", signal.get("blockId", "unknown"))
        values = signal.get("values", [])
        if values:
            # Handle multi-trace (values is list of lists) or single trace
            if isinstance(values[0], list):
                # Multi-trace: get final value of each trace
                input_names = signal.get("inputNames", [])
                for i, trace in enumerate(values):
                    if trace:
                        trace_name = input_names[i] if i < len(input_names) else f"trace_{i}"
                        final_values[trace_name] = trace[-1]
            else:
                # Single trace
                final_values[name] = values[-1]

    return final_values


def run_headless(example_name: str) -> dict:
    """Sync wrapper for async headless simulation."""
    return asyncio.run(run_headless_async(example_name))


def run_python_codegen(zip_path: Path) -> dict:
    """Run Python generated code and return final values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Extract zip
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(tmpdir_path)

        # Find the project directory
        project_dirs = list(tmpdir_path.iterdir())
        project_dir = project_dirs[0]

        # Run main.py
        result = subprocess.run(
            [sys.executable, str(project_dir / "main.py")],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(project_dir)
        )

        if result.returncode != 0:
            raise RuntimeError(f"Python run failed: {result.stderr}")

        # Read results.csv
        results_csv = project_dir / "output" / "results.csv"
        if not results_csv.exists():
            results_csv = project_dir / "results.csv"

        return read_results_csv(results_csv).final_values


def run_docker_codegen(zip_path: Path, language: str) -> dict:
    """Build and run compiled language code in Docker."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Extract zip
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(tmpdir_path)

        # Find the project directory
        project_dirs = list(tmpdir_path.iterdir())
        project_dir = project_dirs[0]

        # Convert to Unix path for Docker
        unix_path = str(project_dir).replace("\\", "/")
        # Handle Windows drive letter
        if len(unix_path) > 1 and unix_path[1] == ':':
            unix_path = "/" + unix_path[0].lower() + unix_path[2:]

        # Docker image and build commands based on language
        if language == "rust":
            docker_image = "rust:1.75"
            # Build using cargo directly - binary is named "simulation" per Cargo.toml
            # Suppress warnings completely with RUSTFLAGS and allow all warnings
            build_cmd = """
                cd /project && \
                mkdir -p output && \
                RUSTFLAGS="-A warnings" cargo build --release && \
                ./target/release/simulation
            """
        elif language == "cpp" or language == "c":
            # Use debian-based image and install cmake
            docker_image = "gcc:13"
            # Build using CMake directly (install cmake first)
            build_cmd = """
                apt-get update -qq && apt-get install -y -qq cmake > /dev/null 2>&1 && \
                cd /project && \
                mkdir -p build output && \
                cd build && \
                cmake -DCMAKE_BUILD_TYPE=Release .. > /dev/null && \
                make -j$(nproc) > /dev/null 2>&1 && \
                cd .. && \
                ./build/simulation
            """
        else:
            raise RuntimeError(f"Unsupported language: {language}")

        cmd = [
            "docker", "run", "--rm",
            "-v", f"{unix_path}:/project",
            docker_image,
            "bash", "-c", build_cmd
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # Increase timeout for apt-get install
        )

        if result.returncode != 0:
            raise RuntimeError(f"Build/run failed: {result.stderr[:500] if result.stderr else result.stdout[:500]}")

        # Read results.csv
        results_csv = project_dir / "output" / "results.csv"
        if not results_csv.exists():
            results_csv = project_dir / "results.csv"

        if not results_csv.exists():
            raise RuntimeError(f"No results.csv found. stdout: {result.stdout[:300]}")

        return read_results_csv(results_csv).final_values


def compare_values(headless: dict, codegen: dict, tolerance: float = 0.01) -> tuple[bool, float]:
    """Compare two sets of final values. Returns (match, max_error)."""
    comparison = compare_final_values(headless, codegen, tolerance=tolerance)
    return comparison.matches, comparison.max_error


def main():
    print("=" * 60)
    print("Quick Codegen Validation")
    print("=" * 60)

    results = []

    for example in KEY_EXAMPLES:
        print(f"\n{'-' * 60}")
        print(f"Example: {example}")
        print(f"{'-' * 60}")

        # Run headless simulation
        try:
            headless_values = run_headless(example)
            print(f"  Headless final values: {headless_values}")
        except Exception as e:
            print(f"  Headless FAILED: {e}")
            for lang in LANGUAGES:
                results.append((example, lang, False, "Headless failed", 0))
            continue

        for lang in LANGUAGES:
            zip_path = CODEGEN_DIR / f"{example}_{lang}.zip"

            if not zip_path.exists():
                print(f"  {lang}: ZIP not found")
                results.append((example, lang, False, "ZIP not found", 0))
                continue

            try:
                if lang == "python":
                    codegen_values = run_python_codegen(zip_path)
                else:
                    codegen_values = run_docker_codegen(zip_path, lang)

                match, max_error = compare_values(headless_values, codegen_values)

                if match:
                    print(f"  {lang}: PASS (max error: {max_error:.4%})")
                    print(f"         Final values: {codegen_values}")
                    results.append((example, lang, True, "", max_error))
                else:
                    print(f"  {lang}: MISMATCH (max error: {max_error:.4%})")
                    print(f"         Headless: {headless_values}")
                    print(f"         Codegen:  {codegen_values}")
                    results.append((example, lang, False, "Mismatch", max_error))

            except Exception as e:
                print(f"  {lang}: FAILED - {e}")
                results.append((example, lang, False, str(e)[:50], 0))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r[2])
    total = len(results)
    print(f"\nTotal: {passed}/{total} passed ({100*passed/total:.1f}%)")

    print("\nResults by language:")
    for lang in LANGUAGES:
        lang_results = [r for r in results if r[1] == lang]
        lang_passed = sum(1 for r in lang_results if r[2])
        print(f"  {lang}: {lang_passed}/{len(lang_results)}")

    # List failures
    failures = [r for r in results if not r[2]]
    if failures:
        print("\nFailures:")
        for example, lang, _passed, error, _max_error in failures:
            print(f"  - {example} ({lang}): {error}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
