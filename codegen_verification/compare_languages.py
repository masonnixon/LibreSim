#!/usr/bin/env python3
"""Compare codegen results across all 4 languages for each example.

This script checks that all examples produce consistent numerical results
across C, C++, Python, and Rust code generation.

Usage:
    python compare_languages.py [--verbose] [--tolerance 1e-4]
"""

import argparse
import csv
from pathlib import Path

BUILDS_DIR = Path(__file__).parent / "builds"
LANGUAGES = ["c", "cpp", "python", "rust"]
DEFAULT_TOLERANCE = 1e-4  # Tolerance for floating point comparison (0.01%)


def get_example_names():
    """Extract unique example names from build directories."""
    examples = set()
    for d in BUILDS_DIR.iterdir():
        if not d.is_dir():
            continue
        name = d.name
        # Skip headless, fixed, and other special directories
        if "headless" in name or "_fixed" in name or name.startswith("_"):
            continue
        # Extract example name by removing language suffix
        for lang in LANGUAGES:
            suffix = f"_{lang}"
            if name.endswith(suffix):
                example_name = name[: -len(suffix)]
                examples.add(example_name)
                break
    return sorted(examples)


def find_results_file(example_name, lang):
    """Find the results.csv file for an example/language combination."""
    dir_name = f"{example_name}_{lang}"
    build_dir = BUILDS_DIR / dir_name

    if not build_dir.exists():
        return None

    # Look for results.csv in various locations
    possible_paths = [
        build_dir / example_name / "output" / "results.csv",
        build_dir / "output" / "results.csv",
        build_dir / "results.csv",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # Search recursively
    for results_file in build_dir.rglob("results.csv"):
        return results_file

    return None


def read_csv_data(filepath):
    """Read CSV file and return headers and data as list of floats."""
    if filepath is None:
        return None, None

    try:
        with open(filepath, "r") as f:
            reader = csv.reader(f)
            headers = next(reader)
            data = []
            for row in reader:
                try:
                    data.append([float(x) for x in row])
                except ValueError:
                    continue
            return headers, data
    except Exception as e:
        return None, str(e)


def compare_data(data1, data2, tol=DEFAULT_TOLERANCE):
    """Compare two datasets, return (match, max_diff, diff_details).

    Uses combined absolute/relative tolerance:
    - For values near zero (|v| < 1): uses absolute tolerance
    - For larger values: uses relative tolerance
    """
    if data1 is None or data2 is None:
        return False, None, "Missing data"

    if len(data1) != len(data2):
        return False, None, f"Row count mismatch: {len(data1)} vs {len(data2)}"

    if len(data1) == 0:
        return True, 0, "Empty data"

    if len(data1[0]) != len(data2[0]):
        return False, None, f"Column count mismatch: {len(data1[0])} vs {len(data2[0])}"

    max_abs_diff = 0
    max_rel_diff = 0
    max_diff_loc = None
    worst_diff_type = "abs"

    for i, (row1, row2) in enumerate(zip(data1, data2)):
        for j, (v1, v2) in enumerate(zip(row1, row2)):
            abs_diff = abs(v1 - v2)

            # Calculate relative difference (avoid div by zero)
            max_val = max(abs(v1), abs(v2), 1e-10)
            rel_diff = abs_diff / max_val

            # Track worst absolute difference
            if abs_diff > max_abs_diff:
                max_abs_diff = abs_diff

            # Check if this exceeds tolerance
            # Use relative comparison for larger values, absolute for small
            if abs(v1) > 1 or abs(v2) > 1:
                # For larger values, use relative tolerance
                if rel_diff > max_rel_diff:
                    max_rel_diff = rel_diff
                    if rel_diff > tol:
                        max_diff_loc = (i, j, v1, v2, "rel", rel_diff)
                        worst_diff_type = "rel"
            else:
                # For small values, use absolute tolerance
                if abs_diff > tol and abs_diff > max_rel_diff:
                    max_rel_diff = abs_diff
                    max_diff_loc = (i, j, v1, v2, "abs", abs_diff)
                    worst_diff_type = "abs"

    # Determine if we pass
    passes = max_diff_loc is None

    if passes:
        return True, max_rel_diff, f"Match (max_rel={max_rel_diff:.2e}, max_abs={max_abs_diff:.2e})"
    else:
        row, col, v1, v2, diff_type, diff_val = max_diff_loc
        return (
            False,
            diff_val,
            f"Max {diff_type} diff {diff_val:.2e} at row {row}, col {col}: {v1} vs {v2}",
        )


def main():
    parser = argparse.ArgumentParser(description="Compare codegen results across languages")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument(
        "--tolerance", "-t", type=float, default=DEFAULT_TOLERANCE, help="Tolerance for comparison"
    )
    args = parser.parse_args()

    tolerance = args.tolerance
    verbose = args.verbose

    examples = get_example_names()
    print(f"Found {len(examples)} examples to verify")
    print(f"Using tolerance: {tolerance:.0e}\n")

    results = []

    for example in examples:
        print(f"Checking: {example}")

        # Find results files for all languages
        files = {}
        data = {}
        headers_dict = {}
        for lang in LANGUAGES:
            filepath = find_results_file(example, lang)
            files[lang] = filepath
            if filepath:
                hdrs, csv_data = read_csv_data(filepath)
                data[lang] = csv_data
                headers_dict[lang] = hdrs
            else:
                data[lang] = None
                headers_dict[lang] = None

        # Check which languages have results
        available = [lang for lang in LANGUAGES if data[lang] is not None]
        missing = [lang for lang in LANGUAGES if data[lang] is None]

        if len(available) < 2:
            print(f"  SKIP: Only {len(available)} language(s) have results: {available}")
            print(f"  Missing: {missing}")
            results.append((example, "SKIP", missing, "Insufficient data"))
            continue

        # Compare all pairs
        all_match = True
        comparisons = []
        max_overall_diff = 0

        # Use first available as reference
        ref_lang = available[0]
        ref_data = data[ref_lang]

        for lang in available[1:]:
            match, max_diff, details = compare_data(ref_data, data[lang], tolerance)
            comparisons.append((ref_lang, lang, match, max_diff, details))
            if not match:
                all_match = False
            if max_diff is not None and max_diff > max_overall_diff:
                max_overall_diff = max_diff

        if all_match:
            print(f"  PASS: All {len(available)} languages match (max diff: {max_overall_diff:.2e})")
            results.append((example, "PASS", missing, f"max_diff={max_overall_diff:.2e}"))
        else:
            print(f"  FAIL: Inconsistent results")
            for ref, cmp, match, diff, details in comparisons:
                status = "OK" if match else "MISMATCH"
                print(f"    {ref} vs {cmp}: {status} - {details}")
            results.append((example, "FAIL", missing, comparisons))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = [r for r in results if r[1] == "PASS"]
    failed = [r for r in results if r[1] == "FAIL"]
    skipped = [r for r in results if r[1] == "SKIP"]

    print(f"Total examples: {len(results)}")
    print(f"  PASSED: {len(passed)}")
    print(f"  FAILED: {len(failed)}")
    print(f"  SKIPPED: {len(skipped)}")

    if failed:
        print("\nFailed examples:")
        for example, status, missing, details in failed:
            print(f"  - {example}")
            if isinstance(details, list):
                for ref, cmp, match, diff, msg in details:
                    if not match:
                        print(f"      {ref} vs {cmp}: {msg}")

    if skipped:
        print("\nSkipped examples (missing languages):")
        for example, status, missing, details in skipped:
            print(f"  - {example}: missing {missing}")

    # Return exit code based on results
    return 1 if failed else 0


if __name__ == "__main__":
    exit(main())
