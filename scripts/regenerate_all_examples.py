#!/usr/bin/env python3
"""Regenerate all example projects for all languages."""

import json
import sys
from pathlib import Path

# Add backend to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from src.codegen.generator import CodeGenerator, CodeGenerationConfig
from src.codegen.models import Language, IntegrationMethod

EXAMPLES_DIR = REPO_ROOT / "examples"
OUTPUT_DIR = REPO_ROOT / "codegen_verification"

LANGUAGES = [Language.PYTHON, Language.CPP, Language.C, Language.RUST]


def regenerate_all():
    """Regenerate all examples in all languages."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Get all example JSON files
    examples = sorted(EXAMPLES_DIR.glob("*.json"))
    print(f"Found {len(examples)} example files")

    results = {"success": [], "failed": []}

    for example in examples:
        name = example.stem
        print(f"\n{'='*60}")
        print(f"Regenerating: {name}")
        print(f"{'='*60}")

        # Load the model
        try:
            with open(example) as f:
                model_data = json.load(f)
        except Exception as e:
            print(f"  Failed to load: {e}")
            for lang in LANGUAGES:
                results["failed"].append((f"{name}_{lang.value}", f"Load error: {e}"))
            continue

        for lang in LANGUAGES:
            output_name = f"{name}_{lang.value}.zip"
            output_path = OUTPUT_DIR / output_name

            print(f"  {lang.value}...", end=" ", flush=True)

            try:
                config = CodeGenerationConfig(
                    language=lang,
                    project_name=name,
                    integration_method=IntegrationMethod.RK4,
                    step_size=0.01,
                    stop_time=10.0,
                    start_time=0.0,
                    include_csv_output=True,
                    include_main=True,
                )

                generator = CodeGenerator()
                project = generator.generate(model_data, config)

                # Write the zip file
                with open(output_path, "wb") as f:
                    zip_buffer = project.to_zip()
                    f.write(zip_buffer.getvalue())

                print("OK")
                results["success"].append(f"{name}_{lang.value}")

            except Exception as e:
                print(f"FAILED: {e}")
                results["failed"].append((f"{name}_{lang.value}", str(e)[:100]))

    print(f"\n\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Success: {len(results['success'])}")
    print(f"Failed: {len(results['failed'])}")

    if results['failed']:
        print("\nFailed examples:")
        for name, error in results['failed']:
            print(f"  - {name}: {error}")

    return results


if __name__ == "__main__":
    results = regenerate_all()
    sys.exit(0 if not results["failed"] else 1)
