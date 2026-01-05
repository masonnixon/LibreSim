#!/usr/bin/env python3
"""
Validate code generation by comparing generated code outputs to headless simulation.

This script:
1. Runs headless simulation for each example
2. Builds and runs the generated code for each language
3. Compares results and generates a validation report
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Add backend to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from src.simulation.runner import SimulationRunner
from src.models.model import Model
from src.models.simulation import SimulationConfig

EXAMPLES_DIR = REPO_ROOT / "examples"
CODEGEN_DIR = REPO_ROOT / "codegen_verification"
OUTPUT_DIR = REPO_ROOT / "docs"

LANGUAGES = ["python", "cpp", "c", "rust"]

# Examples with stochastic blocks that should still be validated since codegen now
# uses the same Mersenne Twister RNG as Python's random.Random for reproducibility.
# Keep this set for any examples that still have known RNG differences.
STOCHASTIC_EXAMPLES: set[str] = set()  # Empty - all examples should now match


@dataclass
class ValidationResult:
    """Result of validating a single example/language combination."""
    example: str
    language: str
    headless_success: bool = False
    headless_final_values: dict[str, float] = field(default_factory=dict)
    build_success: bool = False
    build_error: str = ""
    run_success: bool = False
    run_error: str = ""
    codegen_final_values: dict[str, float] = field(default_factory=dict)
    matches: bool = False
    max_error: float = 0.0
    notes: str = ""


async def run_headless_simulation_async(example_path: Path) -> dict[str, Any]:
    """Run headless simulation and return final values."""
    with open(example_path) as f:
        model_data = json.load(f)

    model = Model.model_validate(model_data)

    # Run with the model's specified settings or defaults
    step_size = 0.01
    stop_time = 10.0

    # Check if model has simulation settings (can be either simulationConfig or simulationSettings)
    settings = model_data.get("simulationConfig") or model_data.get("simulationSettings") or {}
    step_size = settings.get("stepSize", step_size)
    stop_time = settings.get("stopTime", stop_time)

    config = SimulationConfig(stop_time=stop_time, step_size=step_size)
    runner = SimulationRunner(model, config)

    await runner.run()

    # Check if simulation completed successfully
    if runner.status.value == "error":
        raise RuntimeError(runner.error_message or "Simulation failed")

    results = runner.get_results()

    # Get final values for each output signal
    final_values = {}
    if results.get("signals"):
        for signal in results["signals"]:
            name = signal.get("name", "")
            values = signal.get("values", [])
            if values:
                # Handle both single-trace and multi-trace cases
                if isinstance(values[0], list):
                    # Multi-trace: get last value from first trace
                    for i, input_name in enumerate(signal.get("inputNames", [])):
                        if values[i]:
                            final_values[input_name] = values[i][-1]
                else:
                    # Single-trace: get last value
                    final_values[name] = values[-1]

    return {
        "success": True,
        "final_values": final_values,
        "num_steps": results.get("statistics", {}).get("totalSteps", 0),
    }


def run_headless_simulation(example_path: Path) -> dict[str, Any]:
    """Sync wrapper for async headless simulation."""
    return asyncio.run(run_headless_simulation_async(example_path))


def build_and_run_codegen(zip_path: Path, language: str) -> dict[str, Any]:
    """Extract, build, and run generated code. Return final CSV values."""
    result = {
        "build_success": False,
        "build_error": "",
        "run_success": False,
        "run_error": "",
        "final_values": {},
    }

    # Use ignore_cleanup_errors=True on Windows to handle locked files
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Extract zip
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(tmpdir_path)
        except Exception as e:
            result["build_error"] = f"Extract failed: {e}"
            return result

        # Find the project directory
        project_dirs = list(tmpdir_path.iterdir())
        if not project_dirs:
            result["build_error"] = "No project directory found in zip"
            return result
        project_dir = project_dirs[0]

        # Make build.sh executable and run it
        build_script = project_dir / "build.sh"
        if not build_script.exists():
            result["build_error"] = "No build.sh found"
            return result

        # For compiled languages (cpp, c, rust), build.sh handles Docker internally
        # So we just run build.sh directly using bash
        if language in ["cpp", "c", "rust"]:
            try:
                # Run build.sh directly - it handles Docker build/run internally
                # Use shell=True on Windows to get proper path handling
                import platform
                if platform.system() == "Windows":
                    # On Windows, run bash with the script in cwd
                    build_result = subprocess.run(
                        ["bash", "build.sh"],
                        capture_output=True,
                        text=True,
                        timeout=300,  # 5 minutes for Docker build + run
                        cwd=str(project_dir),
                    )
                else:
                    build_result = subprocess.run(
                        ["bash", str(build_script)],
                        capture_output=True,
                        text=True,
                        timeout=300,
                        cwd=str(project_dir),
                    )
                if build_result.returncode != 0:
                    # Include both stdout and stderr for better diagnostics
                    error_msg = build_result.stderr or build_result.stdout or "Unknown error"
                    result["build_error"] = error_msg[:500]
                    return result
                result["build_success"] = True
            except subprocess.TimeoutExpired:
                result["build_error"] = "Build timeout (5 min)"
                return result
            except Exception as e:
                result["build_error"] = str(e)
                return result

        elif language == "python":
            # For Python, just run the script directly
            main_script = project_dir / "main.py"
            if not main_script.exists():
                result["build_error"] = "No main.py found"
                return result

            result["build_success"] = True

            try:
                run_result = subprocess.run(
                    [sys.executable, str(main_script)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=str(project_dir)
                )
                if run_result.returncode != 0:
                    result["run_error"] = run_result.stderr[:500] if run_result.stderr else "Unknown error"
                    return result
            except subprocess.TimeoutExpired:
                result["run_error"] = "Run timeout"
                return result
            except Exception as e:
                result["run_error"] = str(e)
                return result

        # Read the results CSV
        results_csv = project_dir / "output" / "results.csv"
        if not results_csv.exists():
            results_csv = project_dir / "results.csv"

        if not results_csv.exists():
            result["run_error"] = "No results.csv found"
            return result

        result["run_success"] = True

        # Parse CSV and get final values
        try:
            with open(results_csv) as f:
                lines = f.readlines()
                if len(lines) < 2:
                    result["run_error"] = "Results CSV is empty"
                    return result

                headers = lines[0].strip().split(",")
                last_line = lines[-1].strip().split(",")

                for i, header in enumerate(headers):
                    if header.lower() != "time" and i < len(last_line):
                        try:
                            result["final_values"][header] = float(last_line[i])
                        except ValueError:
                            pass
        except Exception as e:
            result["run_error"] = f"CSV parse error: {e}"
            return result

    return result


def validate_example(example_name: str) -> list[ValidationResult]:
    """Validate all languages for a single example."""
    results = []
    example_path = EXAMPLES_DIR / f"{example_name}.json"

    if not example_path.exists():
        for lang in LANGUAGES:
            result = ValidationResult(example=example_name, language=lang)
            result.notes = "Example file not found"
            results.append(result)
        return results

    # Run headless simulation
    try:
        headless = run_headless_simulation(example_path)
        headless_success = headless["success"]
        headless_final = headless["final_values"]
    except Exception as e:
        headless_success = False
        headless_final = {}
        headless_error = str(e)

    for lang in LANGUAGES:
        result = ValidationResult(
            example=example_name,
            language=lang,
            headless_success=headless_success,
            headless_final_values=headless_final,
        )

        if not headless_success:
            result.notes = f"Headless failed: {headless_error[:100]}"
            results.append(result)
            continue

        # Find the zip file
        zip_path = CODEGEN_DIR / f"{example_name}_{lang}.zip"
        if not zip_path.exists():
            result.notes = "Codegen zip not found"
            results.append(result)
            continue

        # Build and run
        codegen_result = build_and_run_codegen(zip_path, lang)
        result.build_success = codegen_result["build_success"]
        result.build_error = codegen_result["build_error"]
        result.run_success = codegen_result["run_success"]
        result.run_error = codegen_result["run_error"]
        result.codegen_final_values = codegen_result["final_values"]

        # Compare results
        if result.run_success and result.headless_success:
            max_error = 0.0
            all_match = True

            # Match outputs by name (case-insensitive)
            headless_lower = {k.lower(): v for k, v in headless_final.items()}
            codegen_lower = {k.lower(): v for k, v in result.codegen_final_values.items()}

            for key, headless_val in headless_lower.items():
                if key in codegen_lower:
                    codegen_val = codegen_lower[key]
                    abs_diff = abs(headless_val - codegen_val)

                    # For near-zero values, use absolute error threshold
                    # Both values must be small for this to apply
                    if abs(headless_val) < 1e-6 and abs(codegen_val) < 1e-6:
                        # Both values are essentially zero, consider it a match
                        rel_error = 0.0 if abs_diff < 1e-6 else abs_diff
                    elif abs(headless_val) > 1e-10:
                        rel_error = abs_diff / abs(headless_val)
                    else:
                        rel_error = abs_diff

                    max_error = max(max_error, rel_error)
                    # Use 3% tolerance (0.03) to account for numerical integration drift
                    if rel_error > 0.03:
                        all_match = False

            result.matches = all_match
            result.max_error = max_error

        results.append(result)

    return results


def generate_report(all_results: list[ValidationResult]) -> str:
    """Generate a markdown validation report."""
    lines = []
    lines.append("# Codegen Validation Report")
    lines.append("")
    lines.append("This report compares the outputs of generated code against the headless simulation.")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Example | Python | C++ | C | Rust |")
    lines.append("|---------|--------|-----|---|------|")

    # Group results by example
    examples = {}
    for result in all_results:
        if result.example not in examples:
            examples[result.example] = {}
        examples[result.example][result.language] = result

    for example_name in sorted(examples.keys()):
        row = [example_name]
        for lang in LANGUAGES:
            result = examples[example_name].get(lang)
            if result is None:
                row.append("-")
            elif result.matches:
                row.append("PASS")
            elif not result.build_success:
                row.append("BUILD FAIL")
            elif not result.run_success:
                row.append("RUN FAIL")
            elif not result.headless_success:
                row.append("SIM FAIL")
            else:
                row.append(f"DIFF ({result.max_error:.2%})")
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")

    # Count statistics
    total = len(all_results)
    passed = sum(1 for r in all_results if r.matches)
    build_fail = sum(1 for r in all_results if not r.build_success)
    run_fail = sum(1 for r in all_results if r.build_success and not r.run_success)
    diff_fail = sum(1 for r in all_results if r.run_success and not r.matches)

    lines.append("## Statistics")
    lines.append("")
    lines.append(f"- Total tests: {total}")
    lines.append(f"- Passed: {passed} ({100*passed/total:.1f}%)")
    lines.append(f"- Build failures: {build_fail}")
    lines.append(f"- Run failures: {run_fail}")
    lines.append(f"- Value mismatches: {diff_fail}")
    lines.append("")

    # Detailed failures
    lines.append("## Detailed Failures")
    lines.append("")

    failures = [r for r in all_results if not r.matches]
    if not failures:
        lines.append("No failures!")
    else:
        for result in failures:
            lines.append(f"### {result.example} ({result.language})")
            lines.append("")
            if not result.headless_success:
                lines.append(f"- Headless simulation failed")
            if not result.build_success:
                lines.append(f"- Build failed: {result.build_error[:200]}")
            elif not result.run_success:
                lines.append(f"- Run failed: {result.run_error[:200]}")
            else:
                lines.append(f"- Max relative error: {result.max_error:.4%}")
                lines.append(f"- Headless final values: {result.headless_final_values}")
                lines.append(f"- Codegen final values: {result.codegen_final_values}")
            lines.append("")

    return "\n".join(lines)


def main():
    """Run validation for all examples."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_examples = sorted([p.stem for p in EXAMPLES_DIR.glob("*.json")])
    # Filter out stochastic examples that can't be deterministically compared
    examples = [e for e in all_examples if e not in STOCHASTIC_EXAMPLES]
    skipped = [e for e in all_examples if e in STOCHASTIC_EXAMPLES]

    print(f"Found {len(all_examples)} examples, validating {len(examples)} (skipping {len(skipped)} stochastic)")
    if skipped:
        print(f"  Skipped: {', '.join(skipped)}")

    all_results = []

    for i, example in enumerate(examples):
        print(f"\n[{i+1}/{len(examples)}] Validating: {example}")
        results = validate_example(example)
        all_results.extend(results)

        # Print quick status
        for result in results:
            status = "PASS" if result.matches else "FAIL"
            if not result.build_success:
                status = "BUILD"
            elif not result.run_success:
                status = "RUN"
            print(f"  {result.language}: {status}", end="")
            if result.max_error > 0:
                print(f" (err={result.max_error:.2%})", end="")
            print()

    # Generate report
    report = generate_report(all_results)
    report_path = OUTPUT_DIR / "codegen-validation-report.md"
    with open(report_path, "w") as f:
        f.write(report)

    print(f"\n\nReport written to: {report_path}")

    # Summary
    passed = sum(1 for r in all_results if r.matches)
    total = len(all_results)
    print(f"\nTotal: {passed}/{total} passed ({100*passed/total:.1f}%)")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
